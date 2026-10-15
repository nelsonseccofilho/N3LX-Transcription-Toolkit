# CLI and output contract — local AMD reference

**Applicability:** currently configured local GPU application. The public repository does not yet distribute this CLI.

## Example commands

```powershell
# Routine transcription (default Normal output profile)
whisperxgpu ".\recording.mkv" --model large-v3 --device vulkan --language pt --diarize

# Keep a separate QA report
whisperxgpu ".\recording.mkv" --output-profile quality

# Keep all processing evidence for debugging
whisperxgpu ".\recording.mkv" --output-profile debug

# Disable diarization
whisperxgpu ".\recording.mkv" --no-diarize

# Disable the CTC warmup experiment
whisperxgpu ".\recording.mkv" --no-preload-align
```

## Flags confirmed in the v1.0.0 local script

| Argument | Default | Notes |
| --- | --- | --- |
| `arquivo` | Required | Input media readable by FFmpeg |
| `--model` | `large-v3` | Supported choices: `large-v3`, `medium`; local weights needed |
| `--device` | `vulkan` | Only accepted GPU ASR backend in this script |
| `--language` | `pt` | Other languages not validated for ONNX/DirectML word alignment and rejected |
| `--threads` | `6` | CPU helper and whisper.cpp thread count |
| `--gpu` | `0` | Vulkan device index |
| `--diarize` / `--no-diarize` | Enabled | Optional speaker attribution |
| `--output_dir` | Input-adjacent `transcricoes` | Target folder |
| `--output_format` | `json` | Only JSON supported in local GPU app |
| `--output-profile` | `normal` | `normal` / `quality` / `debug` |
| `--experimental-preload-align` / `--no-preload-align` | Enabled | Synthetic CPU CTC preload |
| `--low-score` | `0.20` | QA threshold for low word alignment score |
| `--long-segment` | `15.0` | QA duration threshold in seconds |
| `--whisper-cli` | Local whisper.cpp executable | Explicit path override |
| `--whisper-model` | Local GGML model file | Explicit path override |

The v1.0.0 local implementation writes files using an input-name, model and timestamp prefix. An output filename is **not** an Evidence ID and should not replace an evidence-management system's own identifiers.

## Output profiles

| Profile | Files kept |
| --- | --- |
| Normal | `*.integrado.json` |
| Quality | `*.integrado.json`, `*.qualidade.json` |
| Debug | Integrated, quality, raw whisper.cpp JSON, full diarization JSON, processing log |

When diarization is disabled, the Debug profile has no diarization JSON. Diagnostic logs and QA reports may contain private absolute input paths—redact before sharing.

## Minimal integrated output shape

```json
{
  "segments": [
    {
      "start": 1.2,
      "end": 2.8,
      "text": "An illustrative, fictional phrase.",
      "words": [
        {
          "word": "An",
          "start": 1.2,
          "end": 1.36,
          "score": 0.82,
          "speaker": "SPEAKER_00"
        }
      ],
      "speaker": "SPEAKER_00"
    }
  ],
  "language": "pt"
}
```

This is a **synthetic schema illustration**, not a real transcribed recording. In the actual output, words may lack a speaker or timestamps when the models could not assign them, and segments may contain words from multiple speakers. A `score` measures the alignment stage, not a calibrated probability of ASR correctness.

## What QA contributes

The quality report records stage status, backend detection, per-stage timing, operator evidence, counts and review flags (for example low alignment scores, long segments, unlabeled words and model-detected overlap). It does **not** correct transcripts automatically.

Raw ASR preserves the pre-alignment recognition output. Full diarization preserves regular and exclusive intervals and detected overlaps. The log records subprocess commands and backend evidence for debugging.

Use [the original recording](PROJECT_STORY.md) to resolve important ambiguity and [validation guidance](VALIDATION.md) to interpret flags.
