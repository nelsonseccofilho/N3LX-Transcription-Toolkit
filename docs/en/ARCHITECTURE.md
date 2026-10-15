# Architecture and data flow

The AMD reference workflow is **not conventional WhisperX with a `--device vulkan` flag**. It combines independently configured executables, models and Python environments.

## Pipeline

```text
Authorized input: .mkv / .mp4 / .mp3 / .wav / ...
        |
        v
FFmpeg: first audio stream -> PCM 16 kHz mono (temporary)
        |
        +--> whisper.cpp: Whisper large-v3, Vulkan AMD GPU
        |       |
        |       +--> temporary ASR JSON, timestamped segments
        |                          |
        +--> Portuguese wav2vec2 CTC ONNX via DirectML
        |       +--> WhisperX-style word alignment/timestamps
        |                          |
        +--> pyannote Community-1 segmentation + embeddings
                via ONNX Runtime DirectML
                +--> regular speaker intervals (may overlap)
                +--> exclusive speaker intervals
                         |
                         v
                assign_word_speakers (exclusive)
                         |
                         v
                 integrated JSON (+ optional QA / debug)
```

**Execution distinctions:** the GPU performs the documented Vulkan and DirectML neural stages. FFmpeg processing, JSON handling, WhisperX CTC post-processing, orchestration and some auxiliary ONNX operations can execute on CPU. Operator counts in logs should distinguish legitimate auxiliary CPU work from an unexpected whole-model fallback.

## Isolated environments

The reference deployment uses:

- A main Python environment for the orchestration script and WhisperX/PyTorch-based processing.
- A separate Python environment for the ONNX/DirectML worker dependencies.
- A separately built whisper.cpp Vulkan executable and local model weights.
- A separate traditional WhisperX CPU installation as a preserved rollback path.

This isolation prevented dependency conflicts during development. Do **not** merge CPU and AMD GPU dependencies into the same environment unless the combination is explicitly tested.

## Important file responsibilities

| File or component | Purpose | Public package status |
| --- | --- | --- |
| `transcrever_gpu.py` | CLI, orchestration, FFmpeg, ASR, alignment, diarization, QA, outputs | Local v1.0.0 source audited for behavior; not yet packaged |
| `alinhamento_directml.py` | Adapter invoked by the main process | Available in development snapshots; release verification pending |
| `alinhamento_directml_worker.py` | Portuguese CTC model worker | Available in development snapshots; release verification pending |
| `diarizacao_directml_worker.py` | ONNX diarization worker | Available in development snapshots; release verification pending |
| `preload_alinhamento.py` | Warms WhisperX CTC code using a synthetic input | Available in development snapshots; release verification pending |
| `onnx_pyannote.py` | External Community-1 ONNX integration | Upstream provenance, revision and license verification pending |
| `segmentation.onnx`, `embedding.onnx` | Diarization weights | Must be acquired under their own license/terms |
| Portuguese CTC `model.onnx`, `vocab.json` | Word alignment model | Must be acquired/exported with reproducible provenance |
| `whisper-cli.exe` and `ggml-large-v3.bin` | ASR executable and model | Separate upstream build/download and hash checks required |

The installed alias `whisperxgpu` is specific to the local reference setup. No public installer currently creates it.

## Model and language boundaries

- Whisper large-v3 is used for ASR; a medium model was also exercised during development.
- The GPU word-alignment adapter was validated for **Portuguese**. The local CLI explicitly rejects other languages for that GPU alignment stage.
- Word attribution uses **exclusive** diarization intervals. The separate **regular** output preserves detected overlap regions when Debug diagnostics are requested.
- Anonymous speaker labels may change across recordings and are not real identity recognition.

## Error handling and evidence

The main application preserves partial integrated output when an alignment or diarization stage fails, while returning a nonzero status. The worker contracts check DirectML availability and returned evidence. The code currently **warns** if Vulkan use is not confirmed in the whisper.cpp log; making GPU-log verification a hard release acceptance gate remains on the public-release checklist.

Debug output is intended for diagnosis. Logs and QA JSON can include absolute input paths and must **never** be uploaded unredacted to public issues or source control.

Read [dependencies](DEPENDENCIES.md), [outputs](OUTPUTS_AND_CLI.md) and [release criteria](RELEASE_CRITERIA.md) before interpreting the reference setup as a distributable installer.
