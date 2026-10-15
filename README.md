# N3LX Transcription Toolkit

**Local media transcription on Windows, with CPU and AMD GPU workflows.**

N3LX Transcription Toolkit is a community-oriented project to make local speech transcription easier to **install, understand, validate, and troubleshoot**. The goal is a reproducible path from an audio or video file to a useful transcript, with timestamps and optional speaker diarization.

> **Public release status: documentation bootstrap.** The author has validated an internal CPU workflow and an AMD GPU prototype, but this repository does **not yet** provide a tested one-command installer or the GPU application source. Please do not assume the instructions reproduce the complete GPU setup on a fresh PC.

## Choose your path

| Your computer | Start here | Status |
| --- | --- | --- |
| Windows PC, CPU only | [CPU setup](docs/en/CPU_SETUP.md) | Upstream WhisperX route documented; clean-machine validation pending |
| Windows PC with AMD GPU | [AMD GPU architecture and prerequisites](docs/en/AMD_GPU_SETUP.md) | Working local reference; reproducible packaging pending |

**[Leia em português (Brasil)](docs/pt-BR/README.md)**

## What the toolkit aims to offer

- Audio and video input through FFmpeg (for example WAV, MP3, MP4, and MKV).
- Portuguese transcription, with additional languages subject to model support.
- Optional word-level timestamps and speaker diarization.
- Machine-readable JSON suitable for review and downstream workflows.
- CPU and AMD GPU configurations kept **separate**, to avoid dependency conflicts.
- Diagnostics that tell users whether intended GPU acceleration actually occurred.
- Clear limitations, troubleshooting, and real-world validation rather than promises of perfect accuracy.

## How the tested AMD setup works

The internal NELX-Whisper-GPU reference implementation is a **multi-component pipeline**, not stock WhisperX with a Vulkan switch:

1. **Speech recognition:** whisper.cpp, Whisper large-v3, Vulkan on AMD GPU.
2. **Word alignment:** Portuguese wav2vec2/CTC through ONNX Runtime DirectML.
3. **Speaker diarization:** pyannote Community-1 through ONNX Runtime DirectML, including regular and exclusive intervals.
4. **Outputs:** integrated JSON with words, timestamps and speaker labels; optional QA and diagnostic files.

DirectML execution can still schedule auxiliary ONNX operations on CPU. This is not the same as silently falling back to CPU for the neural inference. See [AMD GPU setup](docs/en/AMD_GPU_SETUP.md).

## Local validation evidence

On a **Windows 11 Pro / AMD Radeon RX 6600M 8 GB** reference machine:

| Sample | Input duration | Processing time | Notes |
| --- | ---: | ---: | --- |
| Real meeting, full run | 1,080.45 s | 448.93 s | 1,805 aligned words; Vulkan recognition, DirectML alignment and diarization confirmed |
| Short regression sample | 25.00 s | Approximately 31 s across reported timed stages | 47 words; Normal output profile produced only integrated JSON |

The full-run processing time was approximately **2.4× faster than the recording's duration**, not 2.4× faster than the original CPU workflow. A directly comparable CPU-versus-GPU benchmark has **not yet** been published. Automatic QA findings are review flags, not a measured transcription error rate.

See [validation and limitations](docs/en/VALIDATION.md).

## Outputs

The local reference app uses three output profiles:

| Profile | Files retained |
| --- | --- |
| Normal (default) | Integrated transcript JSON |
| Quality | Integrated JSON and QA report |
| Debug | Integrated JSON, QA report, raw ASR JSON, diarization JSON and processing log |

The **Normal** profile has passed a real AMD GPU regression run; the other two profiles still need dedicated hardware regression checks after the recent output change. The implementation is not yet distributed in this repository.

## Documentation

- [CPU setup (Windows / WhisperX)](docs/en/CPU_SETUP.md)
- [AMD GPU setup and architecture](docs/en/AMD_GPU_SETUP.md)
- [Validation and known limitations](docs/en/VALIDATION.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)
- [Security and privacy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Privacy and human review

Keep recordings and transcripts private unless you have permission to share them. A machine transcript may be wrong, especially with overlapping voices, poor connections or background noise. Keep a link to the original recording and verify consequential statements against that source.

Screenshots and sample transcripts will be published only after privacy review; no real client recordings or internal meeting content belong in this public repository.

## Project scope and licensing

This toolkit is **independent** of [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system), which describes one optional evidence-ingestion use case. You can use local transcription for interviews, lectures, meetings, or other permitted media.

A project license has **not yet been selected or added**. The repository is public, but that alone does not grant permission to reuse code. We will review the licensing of our own code, dependencies and model weights before software distribution.

Contributions should follow [Conventional Commits](https://www.conventionalcommits.org/).
