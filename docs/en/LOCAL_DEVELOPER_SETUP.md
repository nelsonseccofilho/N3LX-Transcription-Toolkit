# Developer source layout — November 2026

**Status: developer preview, not a complete public GPU installer.** The Toolkit now publishes recovered first-party sources for its six-stage QA, Git Bash live monitor, evidence JSON exporter and command wrappers. An **earlier first-party worker recovered and adapted** to the QA output contract is now included, but it is not confirmed equivalent to the final Windows-tested worker. Runtime environments, model weights, external ONNX integration and a clean installer are not included.

## Repository map

~~~text
N3LX-Transcription-Toolkit/
├── README.md
├── CHANGELOG.md
├── .gitignore
├── src/n3lx_toolkit/
│   ├── __init__.py
│   ├── qa_unificado.py       Six-stage reference runner (Beam Size 5)
│   ├── monitor.py            Truthful per-stage / ASR-log progress
│   └── export_framework.py   One private framework JSON per input
├── scripts/
│   └── gitbash_commands.sh   transcrever / transcrever_pasta functions
├── tests/
│   └── test_toolkit.py       Synthetic offline tests
└── docs/                     EN/PT-BR architecture and setup
~~~

## External runtime required for AMD GPU transcription

The reference QA script expects a configurable workspace containing:

1. Vulkan-built whisper.cpp at tools/whisper.cpp/build-vulkan-nmake/bin/whisper-cli.exe, plus the authorized models/ggml-large-v3.bin weights.
2. An isolated DirectML inference Python environment at venvs/whispergpu-dml/Scripts/python.exe (NumPy, SciPy, ONNX Runtime DirectML, compatible pyannote dependencies).
3. A separate CTC export/reference environment at venvs/whispergpu-ctc-export/Scripts/python.exe (PyTorch and Transformers, pinned to compatible versions).
4. The Portuguese ONNX CTC model at models/alignment/onnx-pt.staging/model.onnx.
5. The locally acquired Portuguese Wav2Vec2 source directory at models/alignment/wav2vec2-large-xlsr-53-portuguese-source (pytorch_model.bin, config.json, preprocessor_config.json, vocab.json).
6. A compatible **diarizacao_directml_worker.py** using the --input / --output interface. The developer preview now includes a reconstructed candidate; real GPU validation against the final local worker remains pending. Community-1 model weights and the ONNX integration package are external.
7. FFmpeg executable on PATH, Windows Git Bash and an AMD GPU exposing Vulkan and DirectML.

All relative items above are beneath the workspace root. This repository does not download or redistribute models or third-party weights, and does not install external model/integration dependencies. It does **not** claim a fresh clone will run GPU transcription.

## Configure an already working Windows installation

~~~bash
cd "/c/example/N3LX-Transcription-Toolkit"

# Native Windows paths are required when the backend Python is Windows Python:
export N3LX_WORKSPACE="$(cygpath -w "/c/example/_workspace")"
export N3LX_DIARIZATION_WORKER="$(cygpath -w "/c/example/diarizacao_directml_worker.py")"

# Optional: preserve an existing validated local QA executor instead:
# export N3LX_QA_SCRIPT="$(cygpath -w "/c/example/qa_unificado2.py")"

source scripts/gitbash_commands.sh
type transcrever
type transcrever_pasta

# Run ONLY on an authorized recording:
transcrever "/c/example/meeting.mkv"
transcrever_pasta "/c/example/recordings"
~~~

The functions handle path completion, preserve spaces, process compatible extensions (.mkv, .mp4, .mp3, .ogg) sequentially, and write a single result to the media-adjacent **transcricao/original-filename.framework.json**. The other formats remain unverified on real end-to-end hardware in the November cycle; **MKV was demonstrated**.

Intermediate PCM, raw ASR, diarization, model logs and QA reports remain in the separate workspace. An existing different JSON will **not** be silently overwritten. The framework JSON is derived evidence with a human review requirement, not an automatically approved requirement/decision.

## Offline synthetic tests

~~~bash
python -m unittest discover -s tests -p "test_*.py" -v
bash -n scripts/gitbash_commands.sh
python src/n3lx_toolkit/qa_unificado.py --help
~~~

The synthetic tests check exporter integrity, speaker ambiguity, output conflicts, missing QA approval, logging timestamps and decoder/cache settings. They require no GPU models, network or private recordings. **They are not evidence that the new public repository setup has passed real hardware ASR**, or that the reconstructed worker is equivalent to the final approved Windows version.

## Release gate

Before a public installable release: recover and audit the exact working external worker, inspect licenses and model terms, pin all Python/build/model revisions, add authorized installation procedures and a truly clean Windows reproduction, test extra media formats and interrupts, and test WER against a human-reviewed reference. See RELEASE_CRITERIA.md and NOVEMBER_2026_PIPELINE.md.

## Recovered diarization worker and cache

The default path is now `src/n3lx_toolkit/diarizacao_directml_worker.py`. Override `N3LX_ONNX_PYANNOTE_REPO` (checkout containing `onnx_pyannote.py`) and `N3LX_DIARIZATION_MODELS` (segmentation, embedding, Community-1 config and PLDA files) as needed, using native Windows paths. To retain the already validated local worker, set `N3LX_DIARIZATION_WORKER` explicitly. The QA cache fingerprint tracks the worker code and the ONNX/PLDA dependencies, so changes create distinct cached evidence.

The published candidate's interval/output schema passed mocked tests. **Actual DirectML inference and compatibility with the last Windows worker are not yet tested for this version.** See the [worker contract](DIARIZATION_WORKER_CONTRACT.md).

## Read-only worker comparison before any replacement

Use [scripts/auditar_worker_local.py](../../scripts/auditar_worker_local.py) to compare the installed worker with the candidate. The auditor reads only two Python sources, computes SHA-256 and AST-derived structural results, and does not import/execute either file or contact the network. Use [the guided local command](../pt-BR/AUDITORIA_WORKER_LOCAL.md) to download the public candidate and the tool into a temporary directory and inspect the existing local file. **Do not deploy the reconstructed worker because of a structural match alone.**
