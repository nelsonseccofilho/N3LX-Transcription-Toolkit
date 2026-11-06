#!/usr/bin/env python3
"""Read actual QA artifacts and render honest terminal progress (developer preview)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

STAGES = (
    ("preflight", "1. Ambiente e modelos"),
    ("audio_16khz", "2. Extracao de audio 16 kHz"),
    ("ctc_directml", "3. CTC / DirectML: verificacao"),
    ("asr_vulkan", "4. Whisper large-v3 / Vulkan"),
    ("diarization_directml", "5. Diarizacao / DirectML"),
    ("integracao_final", "6. Alinhamento e integracao"),
)
TIMESTAMP = re.compile(rb"\[(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})\]")
ACTIVE = re.compile(r"^==\s+(\w+)\s+==\s*$", re.M)


def clock(seconds: float) -> str:
    n = max(0, int(seconds))
    return f"{n//3600:02}:{(n%3600)//60:02}:{n%60:02}"


def last_asr_seconds(path: Path) -> float | None:
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            handle.seek(max(0, handle.tell() - 131072))
            output = handle.read()
    except OSError:
        return None
    results = TIMESTAMP.findall(output)
    if not results:
        return None
    h, m, s, ms = map(int, results[-1][4:])
    return h * 3600 + m * 60 + s + ms / 1000


def report_path_from(output: str) -> Path | None:
    for line in output.splitlines():
        if line.startswith("Evidencias:"):
            location = line.partition(":")[2].strip()
            return Path(location) / "qa_report.json" if location else None
    return None


def read_report(path: Path | None) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        return {}


def draw(media: str, log_path: Path, elapsed: float, finished: bool = False) -> dict:
    output = log_path.read_text(encoding="utf-8", errors="replace")
    path = report_path_from(output)
    report = read_report(path)
    stages = report.get("stages") or {}
    active = ACTIVE.findall(output)
    current = active[-1] if active else None
    passed = sum((stages.get(key) or {}).get("status") == "PASS" for key, _ in STAGES)
    lines = ["NELX-Whisper-GPU | PROGRESSO UNIFICADO",
             "Arquivo: " + Path(media).name, "Tempo decorrido: " + clock(elapsed),
             "-" * 66]
    for key, name in STAGES:
        stage = stages.get(key) or {}
        state = stage.get("status")
        if state == "PASS":
            label = "CACHE" if (stage.get("details") or {}).get("reused") else "PASS"
        elif state == "FAIL":
            label = "FALHOU"
        elif current == key and not finished:
            label = "EM EXECUCAO"
        else:
            label = "PENDENTE"
        lines.append(f"{name:<46} {label}")
    lines += ["-" * 66, f"Etapas aprovadas: {passed}/6"]
    if current == "asr_vulkan" and (stages.get(current) or {}).get("status") != "PASS":
        seconds = last_asr_seconds(path.parent / "asr.log") if path else None
        duration = (stages.get("audio_16khz") or {}).get("details", {}).get("duration_seconds")
        if seconds is not None and isinstance(duration, (int, float)) and duration > 0:
            ratio = min(1.0, max(0.0, seconds / duration))
            fill = int(20 * ratio)
            lines.append(f"ASR: [{'#'*fill}{'.'*(20-fill)}] {ratio*100:5.1f}% do audio")
            lines.append("Trecho processado: " + clock(seconds) + " / " + clock(duration))
        else:
            lines.append("ASR ativo: sem timestamp parcial verificavel.")
    elif current and not finished:
        lines.append("Etapa ativa; sem percentual parcial medido.")
    if finished:
        lines.append("Processamento encerrado; conferindo QA.")
    lines.append("Percentuais somente quando medidos pelo motor.")
    sys.stdout.write("\x1b[2J\x1b[H" + "\n".join(lines) + "\n")
    sys.stdout.flush()
    return {"output": output, "report": report, "report_path": path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified QA live progress panel")
    parser.add_argument("--qa", required=True, type=Path)
    parser.add_argument("--input", required=True)
    parser.add_argument("--modo", choices=("completo",), default="completo")
    args = parser.parse_args()
    if not args.qa.is_file():
        print("QA script not found: " + str(args.qa), file=sys.stderr)
        return 2

    project = Path(__file__).resolve().parents[2]
    workspace = Path(os.environ.get("N3LX_WORKSPACE", str(project.parent / "_workspace"))).expanduser()
    workspace.joinpath("qa").mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix="painel-execucao-", suffix=".log", dir=workspace / "qa")
    log = Path(filename)
    started = time.monotonic()
    process = None
    try:
        with os.fdopen(fd, "w", encoding="utf-8", buffering=1) as stream:
            process = subprocess.Popen(
                [sys.executable, "-u", str(args.qa), "--input", args.input, "--modo", args.modo],
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
            )
            while process.poll() is None:
                draw(args.input, log, time.monotonic() - started)
                time.sleep(2)
            result = process.wait()
        final = draw(args.input, log, time.monotonic() - started, finished=True)
        good = all((final["report"].get("stages", {}).get(key) or {}).get("status") == "PASS"
                   for key, _ in STAGES)
        if result != 0 or not good or "RESULTADO FINAL: QA_END_TO_END_PASS" not in final["output"]:
            print("\nFALHA: QA nao aprovado; ultimas linhas:")
            print("\n".join(final["output"].splitlines()[-25:]))
            print("Log preservado:", log)
            return 1
        path = final["report_path"]
        if not path or not path.is_file():
            print("Relatorio ausente. Log:", log)
            return 1
        print("\nPASS: todas as 6 etapas")
        print("Relatorio:", path)
        print("RESULTADO FINAL: QA_END_TO_END_PASS")
        log.unlink(missing_ok=True)
        return 0
    except KeyboardInterrupt:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=15)
            except (OSError, subprocess.TimeoutExpired):
                pass
        print("\nInterrompido. Log preservado:", log)
        return 130
    except Exception as error:
        print(f"ERRO: monitor: {type(error).__name__}: {error}")
        print("Log preservado:", log)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
