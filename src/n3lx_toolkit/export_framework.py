#!/usr/bin/env python3
"""Export one privacy-aware framework JSON from successful local QA artifacts."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import tempfile

SCHEMA = "nelx.framework-transcript.v1"
STAGES = ("preflight", "audio_16khz", "ctc_directml", "asr_vulkan",
          "diarization_directml", "integracao_final")


def load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected JSON object: " + str(path))
    return obj


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ms(value) -> int:
    return round(float(value) * 1000)


def mixed_parts(words: list[dict]) -> list[dict]:
    result = []
    for word in words:
        speaker = word.get("speaker")
        if not result or result[-1]["speaker_id"] != speaker:
            result.append({"speaker_id": speaker, "tokens": [],
                           "start_ms": None, "end_ms": None})
        group = result[-1]
        group["tokens"].append(str(word.get("word", "")))
        if word.get("start") is not None and word.get("end") is not None:
            start, end = ms(word["start"]), ms(word["end"])
            group["start_ms"] = min(group["start_ms"], start) if group["start_ms"] is not None else start
            group["end_ms"] = max(group["end_ms"], end) if group["end_ms"] is not None else end
    for group in result:
        group["text_unreviewed"] = " ".join(group.pop("tokens"))
    return result


def make_export(media: Path, integrated_path: Path, qa_path: Path, quality_path: Path) -> dict:
    if not media.is_file():
        raise FileNotFoundError(media)
    transcript, qa, quality = (load(p) for p in (integrated_path, qa_path, quality_path))
    if any((qa.get("stages", {}).get(key) or {}).get("status") != "PASS" for key in STAGES):
        raise ValueError("All six QA stages must PASS")
    if quality.get("status") != "PASS" or transcript.get("language") != "pt":
        raise ValueError("Integration has not passed the Portuguese profile")
    raw_segments = transcript.get("segments")
    if not isinstance(raw_segments, list) or not raw_segments:
        raise ValueError("No transcript segments")
    if quality.get("segments") != len(raw_segments):
        raise ValueError("Quality/segment count mismatch")
    if qa.get("source_bytes") != media.stat().st_size:
        raise ValueError("QA media size mismatch")
    if PureWindowsPath(str(qa.get("source", ""))).name.casefold() != media.name.casefold():
        raise ValueError("QA media filename mismatch")
    if os.name == "nt" and os.path.normcase(os.path.abspath(str(qa.get("source", "")))) != os.path.normcase(os.path.abspath(str(media))):
        raise ValueError("QA media path mismatch")

    media_hash = sha256(media)
    match = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[ _]\d{2}-\d{2}-\d{2})?", media.name)
    date = match.group(1) if match else None
    warnings = quality.get("warnings", [])
    by_segment = defaultdict(set)
    counts = Counter()
    for warning in warnings if isinstance(warnings, list) else []:
        if isinstance(warning, dict):
            issue = str(warning.get("issue", "unknown"))
            counts[issue] += 1
            if isinstance(warning.get("segment"), int):
                by_segment[warning["segment"]].add(issue)

    segments = []
    speakers = set()
    mixed_count = 0
    for index, segment in enumerate(raw_segments):
        original_text = segment.get("text")
        words = segment.get("words", [])
        if not isinstance(original_text, str) or not isinstance(words, list):
            raise ValueError("Invalid original transcript segment")
        start, end = ms(segment["start"]), ms(segment["end"])
        if start < 0 or end <= start:
            raise ValueError("Invalid segment timing")
        labels = sorted({str(w["speaker"]) for w in words
                         if isinstance(w, dict) and w.get("speaker")})
        speakers.update(labels)
        flags = set()
        if len(labels) > 1:
            flags.add("MULTIPLE_AUTO_SPEAKERS")
            mixed_count += 1
        if not labels:
            flags.add("SPEAKER_UNASSIGNED")
        if any(isinstance(w, dict) and (w.get("start") is None or w.get("end") is None) for w in words):
            flags.add("WORD_ALIGNMENT_INCOMPLETE")
        flags.update("QA_" + issue.upper() for issue in by_segment.get(index, set()))
        entry = {"id": f"SEG-{index+1:04d}", "start_ms": start, "end_ms": end,
                 "speaker_id": labels[0] if len(labels) == 1 else None,
                 "text": original_text}
        if len(labels) > 1:
            entry["speaker_candidates"] = labels
            entry["speaker_parts_unreviewed"] = mixed_parts(words)
        if flags:
            entry["review_flags"] = sorted(flags)
        segments.append(entry)

    blocks = []
    for block_index in sorted({s["start_ms"] // 180000 for s in segments}):
        current = [s for s in segments if s["start_ms"] // 180000 == block_index]
        blocks.append({"id": f"BLK-{block_index+1:04d}",
                       "start_ms": current[0]["start_ms"],
                       "end_ms": current[-1]["end_ms"],
                       "first_segment_id": current[0]["id"],
                       "last_segment_id": current[-1]["id"]})

    qa_version = str(qa.get("qa_version", "unknown"))
    metadata = transcript.get("metadata") or {}
    duration = (qa.get("stages", {}).get("audio_16khz") or {}).get("details", {}).get("duration_seconds")
    return {
        "schema": SCHEMA,
        "evidence": {
            "id": f"EVD-{date or 'UNDATED'}-ASR-{media_hash[:12].upper()}",
            "type": "machine_generated_transcript", "ownership": "PROJECT_OWNED",
            "authority": "DERIVED", "review_status": "UNREVIEWED",
            "language": "pt", "recording_date_from_filename": date,
            "recording_date_verified": False, "derived_requirements": [],
            "derived_decisions": [],
        },
        "source": {"filename": media.name, "media_sha256": media_hash,
                   "size_bytes": media.stat().st_size,
                   "duration_ms": ms(duration) if duration is not None else None,
                   "local_location_hint": "../" + media.name,
                   "location_hint_scope": "relative_to_transcricao_folder"},
        "transcription": {
            "engine": "NELX-Whisper-GPU", "qa_profile": qa_version,
            "asr_model": "Whisper large-v3",
            "asr_beam_size": 5 if qa_version.endswith("-bs5") else None,
            "asr_backend": metadata.get("backend_asr"),
            "alignment_model": "wav2vec2-large-xlsr-53-portuguese",
            "alignment_backend": metadata.get("backend_alinhamento"),
            "diarization_model": "pyannote-community-1",
            "diarization_backend": metadata.get("backend_diarizacao"),
            "speaker_identities_verified": False,
            "integrated_source_sha256": sha256(integrated_path),
            "quality_source_sha256": sha256(quality_path),
        },
        "technical_quality": {
            "pipeline_status": "PASS",
            "alignment_word_coverage": quality.get("word_coverage"),
            "aligned_word_speaker_coverage": quality.get("speaker_coverage"),
            "words_total": quality.get("words_total"), "words_aligned": quality.get("words_aligned"),
            "words_with_speaker": quality.get("words_with_speaker"),
            "segment_count": len(segments), "mixed_speaker_segments": mixed_count,
            "warning_counts": dict(sorted(counts.items())),
            "recognition_accuracy_evaluated": False,
        },
        "speakers": [{"id": s, "name": None, "identity_verified": False} for s in sorted(speakers)],
        "blocks": blocks, "segments": segments,
        "ingestion_policy": {
            "needs_human_review": True,
            "machine_transcript_is_not_approved_requirement": True,
            "do_not_publish_to_public_framework": True,
        },
    }


def write_new_or_identical(path: Path, value: dict) -> str:
    contents = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() == contents:
            return "REUSED_IDENTICAL"
        raise FileExistsError("Different existing output preserved: " + str(path))
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix=".tmp") as stream:
        temporary = Path(stream.name)
        stream.write(contents)
    try:
        with path.open("xb") as target:
            target.write(temporary.read_bytes())
    except FileExistsError:
        if path.read_bytes() == contents:
            return "REUSED_IDENTICAL"
        raise
    finally:
        temporary.unlink(missing_ok=True)
    return "CREATED"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export one private framework transcript")
    for option in ("media", "integrado", "qa-report", "qualidade", "saida"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    payload = make_export(args.media, args.integrado, args.qa_report, args.qualidade)
    action = write_new_or_identical(args.saida, payload)
    print(f"{action}: {args.saida}")
    print("EVIDENCE_ID:", payload["evidence"]["id"])
    print("SEGMENTS:", len(payload["segments"]), "| REVIEW: UNREVIEWED")
    print("RESULTADO FINAL: PASS_EXPORT_FRAMEWORK_JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
