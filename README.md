# N3LX Transcription Toolkit

**No CUDA should not mean no acceleration.**

**Local audio and video transcription on Windows, using a CPU or an AMD GPU.**

[Português (Brasil)](docs/pt-BR/README.md) · [Project story](docs/en/PROJECT_STORY.md) · [Dependency inventory](docs/en/DEPENDENCIES.md) · [Release status](docs/en/RELEASE_CRITERIA.md)

## Why this project exists

This project was developed to meet the media-transcription and evidence-ingestion needs of the [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system).

I needed to process recordings faster than my existing CPU-based WhisperX workflow, but my computer had an **AMD GPU—not an NVIDIA GPU with CUDA support**. Rather than treating this hardware limitation as a blocker, I built and progressively validated a local AMD acceleration pipeline.

The resulting toolkit documents **two independent paths**:

- **CPU:** conventional WhisperX, suitable for Windows machines without a supported dedicated GPU.
- **AMD GPU:** a custom pipeline using whisper.cpp + Vulkan for speech recognition and ONNX Runtime + DirectML for Portuguese alignment and speaker diarization.

The operating framework inspired this project, but the Toolkit is useful independently for authorized interviews, lectures, meetings and media archives. It does **not** require the operating framework.

## Choose your environment

| Path | Start here | Current public status |
| --- | --- | --- |
| CPU / no dedicated GPU | [CPU installation](docs/en/CPU_SETUP.md) | Instructions based on upstream WhisperX; independent clean-install verification pending |
| AMD GPU on Windows | [AMD architecture and setup](docs/en/AMD_GPU_SETUP.md) | Functioning local reference; complete public install package pending |
| Want to understand the internals? | [Architecture](docs/en/ARCHITECTURE.md) | Based on inspected source and test logs |
| Want an exact list of requirements? | [Dependency inventory](docs/en/DEPENDENCIES.md) | Components identified; exact package locks pending |
| Want to reproduce the results? | [Validation](docs/en/VALIDATION.md) | Local reference test evidence; no independently measured WER |
| Need the current delivery status? | [Release criteria](docs/en/RELEASE_CRITERIA.md) | Software packaging and license review pending |

> **Important release distinction:** The private/local **GPU application v1.0.0** has passed an end-to-end meeting test and its default output-profile regression. **The public repository is currently documentation-first; it is not yet a ready-to-install v1.0.0 software release.** Copying or cloning this repository will not yet install `whisperxgpu`.

## Reference hardware: real, non-CUDA results

| Component | Validated reference machine |
| --- | --- |
| Operating system | Windows 11 Pro |
| CPU | AMD Ryzen 5 5500, 3.60 GHz |
| RAM | 24 GB installed |
| GPU | AMD Radeon RX 6600M, 8 GB dedicated VRAM |
| CUDA / NVIDIA | **Not required or used** |

On this consumer AMD system, a 1,080.45-second recording completed in **448.93 seconds (7 min 29 s)**, equivalent to approximately **2.4× real-time throughput** (media duration divided by processing time). The run generated **1,805 word alignments** and confirmed Vulkan ASR plus DirectML alignment and diarization.

This is **not** a measured speedup against CPU WhisperX. CPU-vs-GPU accuracy and speed comparisons with matched settings are still pending. Other CPUs, Radeon devices, drivers, microphones or recordings can produce different results.

[Read the complete benchmark context](docs/en/VALIDATION.md).

## Capabilities demonstrated by the AMD reference

- Decode common FFmpeg-supported media into 16 kHz mono PCM.
- Run Whisper **large-v3** recognition through **whisper.cpp Vulkan** on an AMD Radeon GPU.
- Align Portuguese words through an ONNX wav2vec2/CTC model on **DirectML**.
- Run **pyannote Community-1** speaker diarization through ONNX/DirectML.
- Preserve regular speaker intervals and use exclusive intervals for word attribution.
- Detect some voice-overlap regions for human review.
- Output a WhisperX-style integrated JSON with text, timestamps and anonymous speaker labels.
- Preload the CPU-side CTC alignment code concurrently with Vulkan recognition.
- Select Normal, Quality or Debug output profiles without changing the inference pipeline.

These are **local test results**—not universal compatibility or accuracy guarantees.

## Quick reference: local GPU CLI

For a machine **already configured with the local reference application**:

```powershell
whisperxgpu ".\meeting.mkv" --model large-v3 --device vulkan --diarize --output_format json --language pt --threads 6
```

The app defaults to the **Normal** output profile, which saves only an integrated JSON. Optional flags: `--output-profile quality` for integrated JSON plus QA, or `--output-profile debug` for all five diagnostic outputs. The local script supports Portuguese alignment only; it rejects other alignment languages rather than pretending they work.

**Do not run this command on a fresh clone**: the GPU app and model installation procedure are not yet distributed. See [the full dependency inventory](docs/en/DEPENDENCIES.md).

## What this toolkit is—and is not

It is a **local transcription tool**, not a source of absolute truth. Source recordings are primary evidence; transcripts help people navigate and review them. A word-alignment score does not measure transcription accuracy, and `SPEAKER_00` does not identify a person by name.

This repository does not contain client data, private recordings, or unredacted terminal screenshots. More accessible user guides, sanitized images and one-command setup are goals for the public release, not claims about the current contents.

## Documentation map

- [Project origin and motivation](docs/en/PROJECT_STORY.md)
- [Evolution and engineering decisions](docs/en/DEVELOPMENT_HISTORY.md)
- [CPU installation](docs/en/CPU_SETUP.md)
- [AMD GPU setup](docs/en/AMD_GPU_SETUP.md)
- [Architecture and data flow](docs/en/ARCHITECTURE.md)
- [Dependencies and what remains to lock](docs/en/DEPENDENCIES.md)
- [JSON outputs and CLI contract](docs/en/OUTPUTS_AND_CLI.md)
- [Reproducibility and clean-install plan](docs/en/REPRODUCIBILITY.md)
- [Benchmarks and limitations](docs/en/VALIDATION.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md)
- [Public release checklist](docs/en/RELEASE_CRITERIA.md)
- [Contributions](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## License and contributions

**Licensing is under review.** Until a license is selected and published, public visibility is not permission to copy or redistribute project source. Third-party code and model weights have separate licenses and access requirements; these must be checked before bundling.

All commits use [Conventional Commits](https://www.conventionalcommits.org/), in English. Please avoid publishing private media or personal information in issues or pull requests.
