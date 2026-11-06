#!/usr/bin/env python3
"""NELX-Whisper-GPU: QA consolidado e retomavel para video local (Windows).

PUBLIC DEVELOPER SNAPSHOT: requires separately acquired models, isolated Python
interpreters, whisper.cpp Vulkan and an external N3LX_DIARIZATION_WORKER.
Not validated as a clean install from this repository alone.

Nao instala pacotes, nao altera modelos e nao envia audio a servicos externos.
Preserva artefatos entre execucoes do mesmo arquivo de origem. Reutiliza as
evidencias aprovadas e executa alinhamento forcado CTC via ONNX/DirectML,
atribuindo palavras a intervalos exclusivos da diarizacao. O resultado so
passa se cumprir os criterios explicitados de cobertura e operacoes GPU.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import wave

VERSION = "2026-11-06.2-bs5"
CACHE_VERSION = "2026-11-06.1-bs5-public1"
# Explicit source required; never ship a real or private recording path.

# Scripts executados no ambiente de exportacao e no ambiente de inferencia,
# sem misturar versoes de Transformers e Hugging Face Hub entre os venvs.
PREPARE_CTC = r'''
import os, sys, wave, tempfile
from pathlib import Path
import numpy as np
wav, target = map(Path, sys.argv[1:3])
with wave.open(str(wav), 'rb') as f:
    assert f.getnchannels() == 1 and f.getframerate() == 16000 and f.getsampwidth() == 2
    raw = f.readframes(3 * 16000)
x = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0
assert len(x) >= 3 * 16000, 'Audio inferior a tres segundos'
inputs = {}
for seconds in (2, 3):
    a = x[:seconds * 16000].copy()
    # Normalizacao local equivalente a do extrator de features wav2vec2.
    a -= a.mean()
    a /= np.sqrt(np.mean(a * a) + 1.0e-7)
    inputs[f'audio{seconds}'] = a.reshape(1, -1).astype(np.float32)
fd, temporary = tempfile.mkstemp(prefix='ctc-input-', suffix='.npz', dir=target.parent)
os.close(fd)
try:
    np.savez_compressed(temporary, **inputs)
    if target.exists():
        raise FileExistsError(target)
    os.replace(temporary, target)
finally:
    if os.path.exists(temporary): os.unlink(temporary)
print('CTC: entradas de 2s e 3s salvas')
'''

TORCH_CTC = r'''
import os, sys, tempfile
from pathlib import Path
import numpy as np
import torch
from transformers import Wav2Vec2ForCTC
source, inputs, target = map(Path, sys.argv[1:4])
torch.set_num_threads(4)
model, info = Wav2Vec2ForCTC.from_pretrained(
    str(source), local_files_only=True, use_safetensors=False,
    weights_only=True, output_loading_info=True)
assert not info.get('missing_keys') and not info.get('mismatched_keys'), 'Pesos CTC incompatíveis'
model.eval()
data = np.load(inputs, allow_pickle=False)
outputs = {}
with torch.inference_mode():
    for seconds in (2, 3):
        sample = torch.from_numpy(data[f'audio{seconds}'])
        logits = model(sample).logits.detach().numpy()
        assert np.isfinite(logits).all()
        outputs[f'logits{seconds}'] = logits.astype(np.float32)
        print(f'PyTorch CTC {seconds}s: {logits.shape}', flush=True)
fd, temporary = tempfile.mkstemp(prefix='ctc-ref-', suffix='.npz', dir=target.parent)
os.close(fd)
try:
    np.savez_compressed(temporary, **outputs)
    if target.exists():
        raise FileExistsError(target)
    os.replace(temporary, target)
finally:
    if os.path.exists(temporary): os.unlink(temporary)
'''

DML_CTC = r'''
import json, os, sys, tempfile
from pathlib import Path
from collections import Counter
import numpy as np
import onnxruntime as ort
model, input_file, ref_file, target = map(Path, sys.argv[1:5])
assert 'DmlExecutionProvider' in ort.get_available_providers(), 'DirectML ausente'
options = ort.SessionOptions()
options.enable_mem_pattern = False
options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
options.enable_profiling = True
options.profile_file_prefix = str(target.parent / 'ctc-profile')
session = ort.InferenceSession(str(model), sess_options=options,
    providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
assert 'DmlExecutionProvider' in session.get_providers()
assert len(session.get_inputs()) == 1 and len(session.get_outputs()) == 1
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
inputs = np.load(input_file, allow_pickle=False)
ref = np.load(ref_file, allow_pickle=False)
metrics = {}
for seconds in (2, 3):
    waveform = inputs[f'audio{seconds}']
    actual = session.run([output_name], {input_name: waveform})[0]
    expected = ref[f'logits{seconds}']
    assert actual.shape == expected.shape, (seconds, actual.shape, expected.shape)
    assert np.isfinite(actual).all(), 'Logits ONNX nao finitos'
    diff = np.abs(actual - expected)
    agreement = float((actual.argmax(axis=-1) == expected.argmax(axis=-1)).mean())
    stats = {
        'shape': list(actual.shape),
        'mean_abs': float(diff.mean()),
        'p99_abs': float(np.quantile(diff, .99)),
        'max_abs': float(diff.max()),
        'token_argmax_agreement': agreement,
    }
    print(f'CTC {seconds}s: {stats}', flush=True)
    metrics[str(seconds)] = stats
    # Critério conservador de equivalencia para detectar conversao defeituosa.
    assert stats['mean_abs'] < .15 and stats['p99_abs'] < .75 and agreement >= .90, (
        f'Equivalencia CTC insuficiente ({seconds}s): {stats}')
profile_path = Path(session.end_profiling())
try:
    events = json.loads(profile_path.read_text(encoding='utf-8'))
    counts = Counter(event.get('args', {}).get('provider', 'desconhecido')
                     for event in events if event.get('cat') == 'Node')
finally:
    profile_path.unlink(missing_ok=True)
print('CTC operadores por provider:', dict(counts), flush=True)
assert counts.get('DmlExecutionProvider', 0) > 0, 'CTC nao executou operacoes DirectML'
payload = {
    'status': 'PASS', 'providers': session.get_providers(),
    'operators': dict(counts), 'comparison': metrics,
    'note': 'Equivalencia de logits em 2 e 3 segundos; NAO e alinhamento por palavra',
}
fd, temporary = tempfile.mkstemp(prefix='ctc-result-', suffix='.json', dir=target.parent)
os.close(fd)
try:
    Path(temporary).write_text(json.dumps(payload, indent=2), encoding='utf-8')
    if target.exists():
        raise FileExistsError(target)
    os.replace(temporary, target)
finally:
    if os.path.exists(temporary): os.unlink(temporary)
'''


CTC_INTEGRATE = 'import json, math, re, sys, unicodedata, wave\nfrom collections import Counter\nfrom pathlib import Path\nimport numpy as np\nimport onnxruntime as ort\nfrom scipy.special import logsumexp\n\nwav_path, asr_path, diar_path, model_path, vocab_path, config_path, result_path, qa_path = map(Path, sys.argv[1:9])\n\n\ndef word_to_ids(text, vocab):\n    """Tokenize only representable letters. Do not invent timings for unsupported words."""\n    out = []\n    chars = [ch for ch in unicodedata.normalize(\'NFC\', text) if ch.isalpha()]\n    if not chars or any(ch.isdigit() for ch in text):\n        return None\n    for char in chars:\n        variants = [char, char.lower(), char.upper()]\n        plain = \'\'.join(ch for ch in unicodedata.normalize(\'NFD\', char)\n                        if unicodedata.category(ch) != \'Mn\')\n        variants.extend([plain, plain.lower(), plain.upper()])\n        match = next((vocab[v] for v in variants if v in vocab), None)\n        if match is None:\n            return None\n        out.append(match)\n    return out or None\n\n\ndef forced_align(logits, target, word_spans, blank, start, end):\n    """CTC Viterbi over blank-interleaved token states, not argmax timestamp guessing."""\n    if logits.ndim != 3 or logits.shape[0] != 1:\n        raise ValueError(\'Formato CTC inesperado\')\n    scores = np.asarray(logits[0], dtype=np.float32)\n    if not np.isfinite(scores).all():\n        raise ValueError(\'Logits CTC nao finitos\')\n    frames, classes = scores.shape\n    if blank < 0 or blank >= classes or any(i < 0 or i >= classes for i in target):\n        raise ValueError(\'IDs do vocabulario incompatíveis com o modelo\')\n    if not target:\n        return []\n    states = np.full(2 * len(target) + 1, blank, dtype=np.int64)\n    states[1::2] = target\n    count = len(states)\n    if frames < len(target):\n        raise ValueError(\'Frames CTC insuficientes para o texto\')\n    jump2 = np.zeros(count, dtype=bool)\n    jump2[3::2] = states[3::2] != states[1:-2:2]\n    logp = scores - logsumexp(scores, axis=-1, keepdims=True)\n    previous = np.full(count, -np.inf, dtype=np.float64)\n    previous[0] = 0.0\n    prev_choices = np.zeros((frames, count), dtype=np.uint8)\n    for frame in range(frames):\n        adv1 = np.empty_like(previous)\n        adv1[0] = -np.inf\n        adv1[1:] = previous[:-1]\n        adv2 = np.full_like(previous, -np.inf)\n        adv2[2:] = previous[:-2]\n        adv2[~jump2] = -np.inf\n        choices = np.stack((previous, adv1, adv2), axis=0)\n        winner = np.argmax(choices, axis=0)\n        prev_choices[frame] = winner\n        previous = choices[winner, np.arange(count)] + logp[frame, states]\n    finish = count - 1 if previous[-1] >= previous[-2] else count - 2\n    if not np.isfinite(previous[finish]):\n        raise ValueError(\'Nao foi encontrado caminho CTC completo\')\n    token_frames = [[] for _ in target]\n    state = finish\n    for frame in range(frames - 1, -1, -1):\n        if state & 1:\n            token_frames[(state - 1) // 2].append(frame)\n        state -= int(prev_choices[frame, state])\n        if state < 0:\n            raise ValueError(\'Backtrack CTC invalido\')\n    result = []\n    for token_begin, token_end in word_spans:\n        frames_for_word = [frame for frames_list in token_frames[token_begin:token_end]\n                           for frame in frames_list]\n        if not frames_for_word:\n            result.append(None)\n            continue\n        left = start + min(frames_for_word) * (end - start) / frames\n        right = start + (max(frames_for_word) + 1) * (end - start) / frames\n        result.append((max(start, left), min(end, right)))\n    return result\n\n\ndef speaker_for(start, end, turns):\n    scored = []\n    for turn in turns:\n        overlap = max(0.0, min(end, float(turn[\'end\'])) - max(start, float(turn[\'start\'])))\n        if overlap > 0:\n            scored.append((overlap, str(turn[\'speaker\'])))\n    if not scored:\n        return None\n    return max(scored, key=lambda item: item[0])[1]\n\n\nwith wave.open(str(wav_path), \'rb\') as stream:\n    if (stream.getnchannels(), stream.getframerate(), stream.getsampwidth()) != (1, 16000, 2):\n        raise ValueError(\'Audio deve ser WAV PCM16 mono 16 kHz\')\n    duration = stream.getnframes() / 16000.0\n    waveform = np.frombuffer(stream.readframes(stream.getnframes()), dtype=\'<i2\').copy()\n\nraw = json.loads(asr_path.read_text(encoding=\'utf-8\'))\ndiarization = json.loads(diar_path.read_text(encoding=\'utf-8\'))\nvocab = json.loads(vocab_path.read_text(encoding=\'utf-8\'))\nconfig = json.loads(config_path.read_text(encoding=\'utf-8\'))\nsource_segments = raw.get(\'transcription\', [])\nturns = sorted(diarization.get(\'exclusive_intervals\', []), key=lambda item: item[\'start\'])\nif not source_segments or not turns:\n    raise ValueError(\'ASR ou diarizacao exclusiva vazios\')\nblank = int(config.get(\'pad_token_id\', vocab.get(\'[PAD]\', 0)))\nseparator = vocab.get(\'|\')\nif separator is None:\n    raise ValueError(\'Token de separacao de palavras ausente no vocabulario\')\n\nif \'DmlExecutionProvider\' not in ort.get_available_providers():\n    raise RuntimeError(\'DirectML indisponivel\')\nopts = ort.SessionOptions()\nopts.enable_mem_pattern = False\nopts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL\nopts.enable_profiling = True\nopts.profile_file_prefix = str(result_path.parent / \'integration-ctc-profile\')\nsession = ort.InferenceSession(str(model_path), sess_options=opts,\n    providers=[\'DmlExecutionProvider\', \'CPUExecutionProvider\'])\nif \'DmlExecutionProvider\' not in session.get_providers():\n    raise RuntimeError(\'Sessao nao utiliza DirectML\')\nif len(session.get_inputs()) != 1 or len(session.get_outputs()) != 1:\n    raise ValueError(\'ONNX CTC com entrada/saida inesperada\')\ninput_name = session.get_inputs()[0].name\noutput_name = session.get_outputs()[0].name\n\nwarnings = []\nsegments = []\nword_total = word_aligned = word_assigned = 0\nctc_success = ctc_attempts = 0\nfor index, segment in enumerate(source_segments):\n    try:\n        start = max(0.0, float(segment[\'offsets\'][\'from\']) / 1000.0)\n        end = min(duration, float(segment[\'offsets\'][\'to\']) / 1000.0)\n        if end <= start:\n            raise ValueError(\'Intervalo ASR invalido\')\n    except (TypeError, KeyError, ValueError) as error:\n        warnings.append({\'segment\': index, \'issue\': \'invalid_asr_offsets\', \'detail\': str(error)})\n        continue\n    text = str(segment.get(\'text\', \'\')).strip()\n    segment_words = []\n    clean = []\n    targets = []\n    spans = []\n    for original in re.findall(r\'\\S+\', text, flags=re.UNICODE):\n        item = {\'word\': original}\n        segment_words.append(item)\n        word_total += 1\n        tokens = word_to_ids(original, vocab)\n        if tokens is None:\n            warnings.append({\'segment\': index, \'issue\': \'unsupported_word\', \'word\': original})\n            continue\n        if clean:\n            targets.append(separator)\n        begin = len(targets)\n        targets.extend(tokens)\n        spans.append((begin, len(targets)))\n        clean.append(item)\n    aligned_positions = []\n    if clean:\n        # Conservatively cap a single ONNX window to 25 seconds to avoid overlarge DML allocations.\n        if end - start > 25.0:\n            warnings.append({\'segment\': index, \'issue\': \'window_too_long\',\n                             \'seconds\': round(end-start, 2)})\n        else:\n            first = max(0, int(start * 16000))\n            last = min(len(waveform), int(end * 16000))\n            values = waveform[first:last].astype(np.float32) / 32768.0\n            if values.size >= 6400:\n                values -= values.mean()\n                values /= np.sqrt(np.mean(values**2) + 1e-7)\n                ctc_attempts += 1\n                try:\n                    logits = session.run([output_name], {input_name: values[None, :]})[0]\n                    aligned_positions = forced_align(logits, targets, spans, blank, start, end)\n                    ctc_success += 1\n                except Exception as error:\n                    warnings.append({\'segment\': index, \'issue\': \'ctc_alignment_failed\',\n                                     \'detail\': f\'{type(error).__name__}: {error}\'})\n            else:\n                warnings.append({\'segment\': index, \'issue\': \'audio_window_too_short\'})\n    for word, position in zip(clean, aligned_positions):\n        if position is None:\n            continue\n        left, right = position\n        if not (0 <= left < right <= duration + 0.01):\n            warnings.append({\'segment\': index, \'issue\': \'invalid_word_timestamp\'})\n            continue\n        word[\'start\'] = round(left, 3)\n        word[\'end\'] = round(right, 3)\n        word_aligned += 1\n        speaker = speaker_for(left, right, turns)\n        if speaker:\n            word[\'speaker\'] = speaker\n            word_assigned += 1\n    votes = Counter(w[\'speaker\'] for w in segment_words if \'speaker\' in w)\n    result_segment = {\'start\': round(start, 3), \'end\': round(end, 3),\n                      \'text\': text, \'words\': segment_words}\n    if votes:\n        result_segment[\'speaker\'] = votes.most_common(1)[0][0]\n    segments.append(result_segment)\n\nprofile_path = Path(session.end_profiling())\ntry:\n    events = json.loads(profile_path.read_text(encoding=\'utf-8\'))\n    by_provider = Counter(ev.get(\'args\', {}).get(\'provider\', \'unknown\') for ev in events\n                          if ev.get(\'cat\') == \'Node\')\nfinally:\n    profile_path.unlink(missing_ok=True)\nif by_provider.get(\'DmlExecutionProvider\', 0) < 1:\n    raise RuntimeError(\'Nenhuma operacao CTC executada no DirectML durante alinhamento\')\n\ncoverage = word_aligned / word_total if word_total else 0.0\nspeaker_coverage = word_assigned / word_aligned if word_aligned else 0.0\nquality = {\n    \'status\': \'PASS\' if coverage >= 0.80 and speaker_coverage >= 0.75 else \'FAIL\',\n    \'language\': \'pt\', \'words_total\': word_total, \'words_aligned\': word_aligned,\n    \'words_with_speaker\': word_assigned, \'word_coverage\': round(coverage, 4),\n    \'speaker_coverage\': round(speaker_coverage, 4),\n    \'ctc_inferences_completed\': ctc_success, \'ctc_inferences_attempted\': ctc_attempts,\n    \'operators\': dict(by_provider), \'segments\': len(segments),\n    \'exclusive_turns\': len(turns), \'warnings\': warnings,\n    \'note\': \'Automatic alignment acceptance is not human evaluation of timestamps or transcription accuracy.\',\n}\n# Produce full evidence even if thresholds were not met, leaving QA stage FAIL for review.\nqa_path.write_text(json.dumps(quality, indent=2, ensure_ascii=False)+\'\\n\', encoding=\'utf-8\')\nresult = {\n    \'segments\': segments, \'language\': \'pt\',\n    \'metadata\': {\'backend_asr\': \'vulkan_confirmado_pelo_log\',\n                 \'backend_alinhamento\': \'onnx_directml_confirmado\',\n                 \'backend_diarizacao\': \'onnx_directml_confirmado\',\n                 \'speaker_assignment\': \'exclusive_speaker_diarization\',\n                 \'alignment_coverage\': round(coverage, 4)},\n}\nresult_path.write_text(json.dumps(result, indent=2, ensure_ascii=False)+\'\\n\', encoding=\'utf-8\')\nprint(\'CTC INTEGRATION:\', json.dumps({k: quality[k] for k in (\'status\',\'segments\',\'words_total\',\n    \'words_aligned\',\'words_with_speaker\',\'word_coverage\',\'speaker_coverage\',\'ctc_inferences_completed\',\'operators\')},\n    ensure_ascii=False), flush=True)\n'


def fmt_exception(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"


def validate_wav(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    with wave.open(str(path), "rb") as stream:
        if (stream.getnchannels(), stream.getframerate(), stream.getsampwidth()) != (1, 16000, 2):
            raise ValueError("WAV nao e PCM 16-bit mono 16 kHz")
        seconds = stream.getnframes() / 16000.0
    if seconds < 3:
        raise ValueError("Audio de teste inferior a tres segundos")
    return {"duration_seconds": round(seconds, 3), "wav_bytes": path.stat().st_size}


def validate_asr(path: Path, log_path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    segments = raw.get("transcription")
    if not isinstance(segments, list) or not segments:
        raise ValueError("ASR nao retornou a lista transcription")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    if "ggml_vulkan:" not in log or "AMD Radeon RX 6600M" not in log:
        raise ValueError("GPU AMD/Vulkan nao confirmada no log")
    if "use gpu    = 1" not in log:
        raise ValueError("Uso efetivo da GPU nao confirmado no log")
    return {"segments": len(segments), "backend": "vulkan_confirmado_pelo_log"}


def validate_diarization(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("backend") != "onnx_directml_confirmado":
        raise ValueError("Backend DirectML da diarizacao nao confirmado")
    ops = data.get("operadores_directml", {})
    if ops.get("segmentacao", 0) < 1 or ops.get("embedding", 0) < 1:
        raise ValueError("Segmentacao ou embedding nao executou DirectML")
    regular = data.get("intervals", [])
    exclusive = data.get("exclusive_intervals", [])
    if not regular or not exclusive:
        raise ValueError("Intervalos de diarizacao ausentes")
    for a, b in zip(sorted(exclusive, key=lambda x: (x["start"], x["end"])),
                    sorted(exclusive, key=lambda x: (x["start"], x["end"]))[1:]):
        if b["start"] < a["end"] - .001:
            raise ValueError("Intervalos exclusivos sobrepostos")
    return {"regular": len(regular), "exclusive": len(exclusive),
            "operadores_directml": ops}


def read_ctc_result(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "PASS" or data.get("operators", {}).get("DmlExecutionProvider", 0) < 1:
        raise ValueError("Evidencia CTC/DirectML invalida")
    if set(data.get("comparison", {})) != {"2", "3"}:
        raise ValueError("Duas duracoes de CTC nao foram comparadas")
    return data


def append_log(log_path: Path, label: str, command: list[str], *, timeout: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as handle:
        handle.write(f"\n=== {label} / {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        handle.write("EXE: " + command[0] + "\n")
        handle.flush()
        try:
            process = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{label}: excedeu o limite de execucao; ver {log_path}") from exc
        if process.returncode != 0:
            tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]
            raise RuntimeError(f"{label}: codigo {process.returncode}; ver {log_path}\n" + "\n".join(tail))


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{description}: {path}")


def report_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                                      prefix="report-", dir=path.parent,
                                      delete=False) as handle:
        temp = Path(handle.name)
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temp, path)  # Apenas o relatorio pertencente a este QA e atualizado.


def main() -> int:
    p = argparse.ArgumentParser(description="QA unificado offline do NELX-Whisper-GPU")
    p.add_argument("--input", type=Path, required=True, help="Gravacao autorizada (.mkv/.mp4/.mp3/.ogg)")
    p.add_argument("--modo", choices=("rapido", "completo"), default="completo")
    args = p.parse_args()

    project = Path(__file__).resolve().parents[2]
    git_root = project.parent
    workspace = Path(os.environ.get("N3LX_WORKSPACE", str(git_root / "_workspace"))).expanduser().resolve()
    diarization = Path(os.environ.get("N3LX_DIARIZATION_WORKER", str(project / "src/diarizacao_directml_worker.py"))).expanduser().resolve()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        print(f"FAIL: video nao localizado: {source}", file=sys.stderr)
        return 2
    # Invalida cache se a gravacao ou algum artefato executavel/modelo mudar.
    signature_parts = [CACHE_VERSION]
    for path in (
        source,
        workspace / "tools/whisper.cpp/build-vulkan-nmake/bin/whisper-cli.exe",
        workspace / "models/ggml-large-v3.bin",
        diarization,
        workspace / "tools/pyannote-onnx-ext-comm-1/utils/audio.py",
        workspace / "models/alignment/onnx-pt.staging/model.onnx",
        workspace / "models/alignment/wav2vec2-large-xlsr-53-portuguese-source/pytorch_model.bin",
        project / "config/alignment-pt-revision.json",
    ):
        if path.is_file():
            stat = path.stat()
            signature_parts.append(f"{path}|{stat.st_size}|{stat.st_mtime_ns}")
        else:
            signature_parts.append(f"{path}|AUSENTE")
    key = hashlib.sha256("\n".join(signature_parts).encode("utf-8")).hexdigest()[:12]
    run_dir = workspace / "qa" / (source.stem + "-" + key)
    run_dir.mkdir(parents=True, exist_ok=True)

    report_path = run_dir / "qa_report.json"
    info = {"qa_version": VERSION, "source": str(source), "source_bytes": source.stat().st_size,
            "mode": args.modo, "artifacts": str(run_dir), "stages": {}}
    print("NELX-Whisper-GPU | QA unificado (offline)", flush=True)
    print("Video:", source, flush=True)
    print("Evidencias:", run_dir, flush=True)

    def stage(name: str, fn) -> bool:
        start = time.perf_counter()
        print(f"\n== {name} ==", flush=True)
        try:
            details = fn()
            state = "PASS"
        except Exception as exc:
            state = "FAIL"
            details = {"error": fmt_exception(exc)}
        info["stages"][name] = {"status": state,
                                 "duration_seconds": round(time.perf_counter() - start, 2),
                                 "details": details}
        report_write(report_path, info)
        print(f"{state}: {name}: {details}", flush=True)
        return state == "PASS"

    cli = workspace / "tools/whisper.cpp/build-vulkan-nmake/bin/whisper-cli.exe"
    ggml = workspace / "models/ggml-large-v3.bin"
    dml = workspace / "venvs/whispergpu-dml/Scripts/python.exe"
    export = workspace / "venvs/whispergpu-ctc-export/Scripts/python.exe"
    # Worker is an external/local prerequisite until source provenance is approved.
    ctc_onnx = workspace / "models/alignment/onnx-pt.staging/model.onnx"
    ctc_source = workspace / "models/alignment/wav2vec2-large-xlsr-53-portuguese-source"
    ffmpeg = shutil.which("ffmpeg")
    wav = run_dir / "audio-16k.wav"
    raw_asr = run_dir / "asr-raw.json"
    asr_log = run_dir / "asr.log"
    diarization_json = run_dir / "diarization.json"
    ctc_inputs = run_dir / "ctc-inputs.npz"
    ctc_reference = run_dir / "ctc-reference.npz"
    ctc_report = run_dir / "ctc-directml.json"
    ctc_log = run_dir / "ctc.log"
    diarization_log = run_dir / "diarization.log"

    def preflight() -> dict:
        for path, name in ((cli, "whisper-cli Vulkan"), (ggml, "large-v3"),
                           (dml, "venv DirectML"), (export, "venv export CTC"),
                           (diarization, "worker diarizacao"), (ctc_onnx, "modelo CTC ONNX"),
                           (ctc_source / "pytorch_model.bin", "pesos CTC"),
                           (ctc_source / "vocab.json", "vocabulario CTC")):
            require_file(path, name)
        if not ffmpeg:
            raise RuntimeError("FFmpeg nao encontrado no PATH")
        for path in (ctc_source / "config.json", ctc_source / "preprocessor_config.json"):
            require_file(path, "configuracao CTC")
        return {"ffmpeg": ffmpeg, "whisper_cli": str(cli), "onnx": str(ctc_onnx)}

    if not stage("preflight", preflight):
        print("\nQA BLOQUEADO: corrigir preflight. Relatorio:", report_path)
        return 2
    if args.modo == "rapido":
        info["stages"]["ctc_directml"] = {"status": "PENDING", "details": "Modo rapido: nao executado"}
        info["stages"]["asr_vulkan"] = {"status": "PENDING", "details": "Modo rapido: nao executado"}
        info["stages"]["diarization_directml"] = {"status": "PENDING", "details": "Modo rapido: nao executado"}
        info["stages"]["integracao_final"] = {"status": "PENDING", "details": "Ainda nao implementada"}
        report_write(report_path, info)
        print("\nRESULTADO: PREFLIGHT_PASS; QA completo nao executado")
        return 0

    def audio_extract() -> dict:
        if wav.exists():
            return {**validate_wav(wav), "reused": True}
        with tempfile.TemporaryDirectory(prefix="ffmpeg-", dir=run_dir) as temporary:
            target = Path(temporary) / "audio.wav"
            append_log(run_dir / "ffmpeg.log", "EXTRACAO", [
                ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(target)], timeout=1200)
            details = validate_wav(target)
            if wav.exists():
                raise FileExistsError(wav)
            target.replace(wav)
        return {**details, "reused": False}

    if not stage("audio_16khz", audio_extract):
        print("\nQA BLOQUEADO: sem WAV valido. Relatorio:", report_path)
        return 2

    def ctc_test() -> dict:
        if ctc_report.exists():
            return {**read_ctc_result(ctc_report), "reused": True}
        if not ctc_inputs.exists():
            append_log(ctc_log, "CTC_INPUT", [str(dml), "-B", "-c", PREPARE_CTC,
                       str(wav), str(ctc_inputs)], timeout=240)
        if not ctc_reference.exists():
            append_log(ctc_log, "CTC_PYTORCH", [str(export), "-B", "-c", TORCH_CTC,
                       str(ctc_source), str(ctc_inputs), str(ctc_reference)], timeout=900)
        append_log(ctc_log, "CTC_ONNX_DIRECTML", [str(dml), "-B", "-c", DML_CTC,
                   str(ctc_onnx), str(ctc_inputs), str(ctc_reference), str(ctc_report)], timeout=1200)
        return {**read_ctc_result(ctc_report), "reused": False}

    stage("ctc_directml", ctc_test)

    def asr_test() -> dict:
        if raw_asr.exists():
            return {**validate_asr(raw_asr, asr_log), "reused": True}
        with tempfile.TemporaryDirectory(prefix="asr-", dir=run_dir) as temporary:
            prefix = Path(temporary) / "asr"
            append_log(asr_log, "WHISPER_VULKAN", [str(cli), "-m", str(ggml),
                "-f", str(wav), "-l", "pt", "-t", "6", "-dev", "0",
                "-mc", "0", "-bs", "5", "-oj", "-of", str(prefix)], timeout=7200)
            result = prefix.with_suffix(".json")
            details = validate_asr(result, asr_log)
            if raw_asr.exists():
                raise FileExistsError(raw_asr)
            shutil.copyfile(result, raw_asr)
        return {**details, "reused": False}

    stage("asr_vulkan", asr_test)

    def diarization_test() -> dict:
        if diarization_json.exists():
            return {**validate_diarization(diarization_json), "reused": True}
        with tempfile.TemporaryDirectory(prefix="diarization-", dir=run_dir) as temporary:
            target = Path(temporary) / "diarization.json"
            append_log(diarization_log, "DIARIZATION_DIRECTML", [str(dml), "-B",
                str(diarization), "--input", str(wav), "--output", str(target)], timeout=3600)
            details = validate_diarization(target)
            if diarization_json.exists():
                raise FileExistsError(diarization_json)
            shutil.copyfile(target, diarization_json)
        return {**details, "reused": False}

    stage("diarization_directml", diarization_test)

    # Integracao sob demanda, usando apenas artefatos ja confirmados pelo QA.
    integrated_json = run_dir / "integrado.json"
    integrated_qa = run_dir / "integracao-qualidade.json"
    integration_log = run_dir / "integracao.log"

    def validate_integrated(result_path: Path, quality_path: Path) -> dict:
        require_file(result_path, "JSON integrado")
        require_file(quality_path, "relatorio de integracao")
        quality = json.loads(quality_path.read_text(encoding="utf-8"))
        integrated = json.loads(result_path.read_text(encoding="utf-8"))
        if quality.get("status") != "PASS":
            raise ValueError("Cobertura de palavras/participantes abaixo do criterio de QA: "
                             + json.dumps({k: quality.get(k) for k in
                                  ("word_coverage", "speaker_coverage", "words_total", "words_aligned")},
                                  ensure_ascii=False))
        if not integrated.get("segments") or integrated.get("language") != "pt":
            raise ValueError("JSON integrado vazio ou idioma divergente")
        if quality.get("operators", {}).get("DmlExecutionProvider", 0) < 1:
            raise ValueError("Operacoes DirectML nao comprovadas na integracao")
        for segment in integrated["segments"]:
            if float(segment["end"]) <= float(segment["start"]):
                raise ValueError("Timestamp de segmento invalido")
            for word in segment.get("words", []):
                if "start" in word or "end" in word:
                    if float(word["end"]) <= float(word["start"]):
                        raise ValueError("Timestamp de palavra invalido")
        return {"segments": len(integrated["segments"]),
                "words_total": quality["words_total"],
                "words_aligned": quality["words_aligned"],
                "words_with_speaker": quality["words_with_speaker"],
                "word_coverage": quality["word_coverage"],
                "speaker_coverage": quality["speaker_coverage"],
                "operators": quality["operators"],
                "integrated_json": str(result_path),
                "quality_report": str(quality_path)}

    def integration_test() -> dict:
        if integrated_json.exists() and integrated_qa.exists():
            return {**validate_integrated(integrated_json, integrated_qa), "reused": True}
        if integrated_json.exists() or integrated_qa.exists():
            raise RuntimeError("Artefatos de integracao incompletos; preservados para analise")
        with tempfile.TemporaryDirectory(prefix="integration-", dir=run_dir) as temporary:
            temp = Path(temporary)
            output = temp / "integrado.json"
            quality = temp / "integracao-qualidade.json"
            append_log(integration_log, "CTC_FORCED_ALIGNMENT_DIRECTML", [
                str(dml), "-B", "-c", CTC_INTEGRATE,
                str(wav), str(raw_asr), str(diarization_json), str(ctc_onnx),
                str(ctc_source / "vocab.json"), str(ctc_source / "config.json"),
                str(output), str(quality)], timeout=7200)
            details = validate_integrated(output, quality)
            if integrated_json.exists() or integrated_qa.exists():
                raise FileExistsError("Saida integrada criada em paralelo")
            shutil.copyfile(output, integrated_json)
            shutil.copyfile(quality, integrated_qa)
            return {**validate_integrated(integrated_json, integrated_qa), "reused": False}

    dependencies = ("ctc_directml", "asr_vulkan", "diarization_directml")
    blocked = [name for name in dependencies if info["stages"][name]["status"] != "PASS"]
    if blocked:
        info["stages"]["integracao_final"] = {
            "status": "PENDING",
            "details": "Etapas predecessoras nao aprovadas: " + ", ".join(blocked)}
        report_write(report_path, info)
        print("PENDING: integracao_final: dependencias nao aprovadas", blocked, flush=True)
    else:
        stage("integracao_final", integration_test)
    print("\n=== RESUMO QA ===")
    for name, state in info["stages"].items():
        print(f"{state['status']:7s} {name}")
    print("Relatorio:", report_path)
    failed = [name for name, state in info["stages"].items() if state["status"] == "FAIL"]
    if failed:
        print("RESULTADO FINAL: QA_PARCIAL_COM_FALHAS -", ", ".join(failed))
        return 2
    if info["stages"]["integracao_final"]["status"] == "PASS":
        print("RESULTADO FINAL: QA_END_TO_END_PASS")
        return 0
    print("RESULTADO FINAL: QA_COMPONENTES_PASS_INTEGRACAO_PENDENTE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario; evidencias concluidas foram preservadas.", file=sys.stderr)
        raise SystemExit(130)
