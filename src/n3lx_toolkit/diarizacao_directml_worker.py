#!/usr/bin/env python3
"""Worker de diarizacao NELX GPU, executado apenas pelo venv DirectML isolado.

Na arquitetura NELX, 'GPU' significa inferencia neural acelerada por DirectML:
algumas operacoes ONNX e o agrupamento PLDA ainda rodam na CPU por necessidade.
Nao existe fallback automatico dos modelos para uma implementacao somente CPU.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("N3LX_WORKSPACE", str(ROOT.parent / "_workspace"))).expanduser().resolve()
REPO = Path(os.environ.get("N3LX_ONNX_PYANNOTE_REPO", str(WORKSPACE / "tools/pyannote-onnx-ext-comm-1"))).expanduser().resolve()
MODELS = Path(os.environ.get("N3LX_DIARIZATION_MODELS", str(WORKSPACE / "models/diarization/onnx-community-1"))).expanduser().resolve()


def validate_local_models() -> None:
    for path in (REPO / "onnx_pyannote.py", MODELS / "segmentation.onnx", MODELS / "embedding.onnx"):
        if not path.is_file():
            raise FileNotFoundError(f"Dependencia externa ausente: {path}")



def load_pipeline(*, profile: bool, profile_dir: Path | None):
    validate_local_models()
    import onnxruntime as ort

    if "DmlExecutionProvider" not in ort.get_available_providers():
        raise RuntimeError("DmlExecutionProvider nao encontrado: abortando sem fallback CPU.")

    sys.path.insert(0, str(REPO))
    from onnx_pyannote import ONNXSpeakerDiarization

    original = ort.InferenceSession

    def dml_session(*args, **kwargs):
        if "sess_options" in kwargs:
            raise RuntimeError("Assinatura ONNX inesperada: sess_options duplicado")
        opts = ort.SessionOptions()
        opts.enable_mem_pattern = False
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        opts.enable_profiling = profile
        if profile and profile_dir is not None:
            opts.profile_file_prefix = str(profile_dir / f"nelx-onnx-profile-{uuid.uuid4().hex}")
        return original(*args, sess_options=opts, **kwargs)

    ort.InferenceSession = dml_session
    try:
        pipeline = ONNXSpeakerDiarization(
            str(MODELS), providers=["DmlExecutionProvider", "CPUExecutionProvider"]
        )
    finally:
        ort.InferenceSession = original

    for name, sess in (("segmentacao", pipeline.segmentation_session),
                       ("embedding", pipeline.embedding_session)):
        if "DmlExecutionProvider" not in sess.get_providers():
            raise RuntimeError(f"Modelo {name} nao inicializou DirectML; sem fallback CPU")
    return pipeline


def operators_by_provider(sess) -> dict[str, int]:
    path = Path(sess.end_profiling())
    try:
        events = json.loads(path.read_text(encoding="utf-8"))
        counts = Counter(
            e.get("args", {}).get("provider", "desconhecido")
            for e in events if e.get("cat") == "Node"
        )
        return dict(counts)
    finally:
        try:
            path.unlink(missing_ok=True)
        except PermissionError:
            # Em Windows, o profiler pode liberar o arquivo apos o encerramento do worker.
            # O diretório temporario da aplicacao sera limpo apos a saida do processo.
            print(f"AVISO DIRECTML: limpeza do profiler adiada: {path.name}", file=sys.stderr, flush=True)


def extract_intervals(annotation, duration: float, *, exclusive: bool) -> list[dict]:
    """Validate and normalize speaker labels without inventing timing."""
    rows = []
    if annotation is None:
        raise ValueError("Community-1 retornou diarizacao ausente")
    for segment, _, label in annotation.itertracks(yield_label=True):
        start, end = float(segment.start), float(segment.end)
        if not (math.isfinite(start) and math.isfinite(end) and
                0 <= start < end <= duration + .2):
            raise ValueError(f"Intervalo invalido: {start}, {end}")
        bounded_end = min(end, duration)
        if bounded_end <= start:
            continue
        rows.append({"start": start, "end": bounded_end, "speaker": str(label)})
    rows.sort(key=lambda item: (item["start"], item["end"], item["speaker"]))
    if exclusive:
        for old, new in zip(rows, rows[1:]):
            if new["start"] < old["end"] - .001:
                raise ValueError("Diarizacao exclusiva com sobreposicao")
    return rows


def run(input_path: Path, output_path: Path) -> None:
    import wave
    with wave.open(str(input_path), "rb") as stream:
        if (stream.getframerate(), stream.getnchannels(), stream.getsampwidth()) != (16000, 1, 2):
            raise RuntimeError("Diarizacao requer WAV PCM16 mono 16 kHz")
        duration = stream.getnframes() / 16000

    pipeline = load_pipeline(profile=True, profile_dir=output_path.parent)
    result = pipeline(str(input_path))
    regular = extract_intervals(result.speaker_diarization, duration, exclusive=False)
    exclusive = extract_intervals(result.exclusive_speaker_diarization, duration, exclusive=True)
    if not regular or not exclusive:
        raise RuntimeError("Diarizacao regular/exclusiva vazia")

    segmentation = operators_by_provider(pipeline.segmentation_session)
    embedding = operators_by_provider(pipeline.embedding_session)
    if segmentation.get("DmlExecutionProvider", 0) < 1:
        raise RuntimeError("Segmentacao nao executou operadores DirectML: sem fallback CPU")
    if embedding.get("DmlExecutionProvider", 0) < 1:
        raise RuntimeError("Embedding nao executou operadores DirectML: sem fallback CPU")

    payload = {
        "backend": "onnx_directml_confirmado",
        "intervals": regular,
        "exclusive_intervals": exclusive,
        "operadores_directml": {
            "segmentacao": segmentation.get("DmlExecutionProvider", 0),
            "embedding": embedding.get("DmlExecutionProvider", 0),
        },
        "operadores_cpu_onnx": {
            "segmentacao": segmentation.get("CPUExecutionProvider", 0),
            "embedding": embedding.get("CPUExecutionProvider", 0),
        },
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(
        f"DirectML confirmado: {payload['operadores_directml']} | "
        f"regular: {len(regular)}, exclusive: {len(exclusive)}", flush=True
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Worker isolado de diarizacao ONNX + DirectML")
    parser.add_argument("--check", action="store_true", help="Verificar disponibilidade e inicializacao DirectML")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.check:
            load_pipeline(profile=False, profile_dir=None)
            print("CHECK DIRECTML OK: modelos carregados com DmlExecutionProvider", flush=True)
        else:
            if args.input is None or args.output is None:
                parser.error("--input e --output sao obrigatorios sem --check")
            run(args.input.resolve(), args.output.resolve())
        return 0
    except Exception as exc:
        print(f"ERRO DIRECTML: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
