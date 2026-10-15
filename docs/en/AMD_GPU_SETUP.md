# AMD GPU workflow — Windows

**Status: validated locally on an AMD Radeon RX 6600M; not yet packaged for reproducible public installation.**

## Do not use the wrong backend

The tested AMD solution is **not** the standard WhisperX CLI with `--device vulkan`. It combines several separately configured components:

| Stage | Tested model/component | Acceleration |
| --- | --- | --- |
| Audio extraction | FFmpeg, mono 16 kHz | CPU / preprocessing |
| Automatic speech recognition | whisper.cpp with Whisper large-v3 | Vulkan (AMD GPU) |
| Word alignment | Portuguese wav2vec2 CTC exported to ONNX | ONNX Runtime DirectML |
| Speaker diarization | pyannote Community-1 ONNX workers | ONNX Runtime DirectML |
| Text integration / QA | Python post-processing | CPU |

The architecture uses isolated Python environments for the GPU alignment and diarization workers. It must never silently claim GPU acceleration when neural model execution moved to CPU. Some **auxiliary ONNX operations on CPU** are expected and should be reported separately.

The prototype also performs an alignment preload in parallel with the ASR stage, then waits for it to complete before alignment. The measured gain on a three-minute sample was approximately 8.8% versus the same GPU pipeline without preload.

## Tested hardware

- Windows 11 Pro.
- AMD Radeon RX 6600M with 8 GB dedicated VRAM.
- Recognition model: Whisper large-v3 via whisper.cpp Vulkan.
- Alignment and diarization: DirectML ONNX model inference.

**Not yet established:** full compatibility across all Radeon products, driver revisions, integrated GPUs, or all AMD architectures.

## What must be published before this becomes an install guide

1. Sanitized and license-reviewed application/worker sources.
2. Exact Python, GPU driver, FFmpeg, whisper.cpp, ONNX Runtime and model revisions.
3. Build and installation instructions for whisper.cpp Vulkan.
4. Safe model acquisition, hashes and any model terms / authorization steps.
5. Dependency locks for isolated environments.
6. Hardware diagnostics and a verified failure policy.
7. A full fresh-machine reproduction test.

The local command `whisperxgpu` is an application-specific entry point on the reference PC. It **is not currently installed by cloning this repository**.

## Diagnostics from the reference run

The full 18-minute run reported `vulkan_confirmado_pelo_log` for ASR and `onnx_directml_confirmado` for alignment and diarization. It also recorded 226,570 DirectML operators and 46,944 auxiliary CPU ONNX operators during alignment. These numbers are *test evidence*, not installation requirements.

See [validation](VALIDATION.md) and [troubleshooting](TROUBLESHOOTING.md).
