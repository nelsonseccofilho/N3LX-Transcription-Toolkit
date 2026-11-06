#!/usr/bin/env python3
"""Read-only, privacy-minimizing comparison of two local Python diarization workers.

This does not execute worker code, access media/model files, send network requests,
or change the installed worker. Structural results do not prove runtime parity.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

EXPECTED_NAMES = (
    "DmlExecutionProvider",
    "ONNXSpeakerDiarization",
    "speaker_diarization",
    "exclusive_speaker_diarization",
    "exclusive_intervals",
    "operadores_directml",
    "segmentacao",
    "embedding",
)
EXPECTED_FUNCTIONS = (
    "load_pipeline",
    "operators_by_provider",
    "run",
    "main",
)


def collect(path: Path) -> dict:
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"), filename="worker.py")
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add(node.value)
    methods: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Discard source spans so comments/whitespace do not alter signatures.
            normalized = ast.dump(node, annotate_fields=True, include_attributes=False)
            methods[node.name] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "required_signals": {key: key in names for key in EXPECTED_NAMES},
        "expected_functions": {key: key in methods for key in EXPECTED_FUNCTIONS},
        "function_digests": methods,
    }


def compare(installed: dict, candidate: dict) -> dict:
    same_file = installed["sha256"] == candidate["sha256"]
    common = set(installed["function_digests"]) & set(candidate["function_digests"])
    changed = sorted(name for name in common
                     if installed["function_digests"][name] != candidate["function_digests"][name])
    only_installed = sorted(set(installed["function_digests"]) - set(candidate["function_digests"]))
    only_candidate = sorted(set(candidate["function_digests"]) - set(installed["function_digests"]))
    missing = sorted(name for name, present in installed["required_signals"].items()
                     if not present and candidate["required_signals"].get(name))
    return {
        "status": ("MATCH_EXATO" if same_file else
                   "DIVERGENCIA_ESTRUTURAL" if (changed or only_installed or only_candidate or missing) else
                   "DIFERENCA_NAO_FUNCIONAL_OU_EXTERNA"),
        "worker_local_sha256": installed["sha256"],
        "worker_publicado_sha256": candidate["sha256"],
        "local_tamanho_bytes": installed["size_bytes"],
        "publicado_tamanho_bytes": candidate["size_bytes"],
        "local_sinais_ausentes": missing,
        "funcoes_modificadas": changed,
        "funcoes_somente_locais": only_installed,
        "funcoes_somente_publicadas": only_candidate,
        "worker_local_tem_intervalos_exclusivos": installed["required_signals"]["exclusive_intervals"],
        "worker_local_tem_verificacao_directml": installed["required_signals"]["DmlExecutionProvider"],
        "observacao": "A comparação estática não comprova equivalência funcional nem execução GPU.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auditoria estrutural local do worker, sem alterar arquivos")
    parser.add_argument("--instalado", required=True, type=Path)
    parser.add_argument("--publicado", required=True, type=Path)
    parser.add_argument("--exigir-identidade", action="store_true", help="Falha se hashes forem diferentes")
    args = parser.parse_args(argv)
    try:
        local = collect(args.instalado.expanduser().resolve())
        published = collect(args.publicado.expanduser().resolve())
    except (OSError, UnicodeError, SyntaxError):
        # Avoid echoing exception text: it may contain private absolute paths.
        print("FALHA: algum arquivo não pode ser lido ou analisado como Python válido.", file=sys.stderr)
        return 2
    result = compare(local, published)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    print("RESULTADO FINAL: " + result["status"])
    if args.exigir_identidade and result["status"] != "MATCH_EXATO":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
