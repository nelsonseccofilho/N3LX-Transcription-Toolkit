# Dependency inventory and provenance

**Scope:** components observed in the functional local reference and development snapshots. This is **not** a fabricated package lock or a claim of a tested clean-machine installer. Exact installed versions, source revisions, hashes and redistributability must be captured before public software release.

## Operating system and hardware

| Requirement | Reference / purpose | Confidence |
| --- | --- | --- |
| Windows | Windows 11 Pro reference | Tested |
| Processor | AMD Ryzen 5 5500, 3.60 GHz | Tested reference, not a minimum spec |
| RAM | 24 GB installed | Tested reference, not a minimum spec |
| GPU | AMD Radeon RX 6600M, 8 GB VRAM | Tested |
| GPU driver | AMD Windows display driver exposing Vulkan and DirectML | Version lock pending |
| CUDA | **Not required** for this AMD design | Architectural fact |
| Disk capacity | Models, Python environments, media and temp WAV need free storage | Exact minimum not measured |
| PowerShell 7 | Used in development and examples | Tested reference |

The CPU installation path does not require an AMD GPU. Its resource needs depend on the model and source duration.

## CPU path: upstream WhisperX

| Component | Function | Status |
| --- | --- | --- |
| Python | Isolated `venv` runtime | Exact compatible version not locked |
| FFmpeg | Media decoding | Exact version not locked |
| `whisperx` | ASR, alignment and speaker tooling | Exact upstream version not locked |
| PyTorch and its dependencies | WhisperX runtime | Resolve against chosen WhisperX release |
| Hugging Face account / model terms / optional read token | Needed for applicable diarization models | Follow upstream terms; never commit tokens |

Reference CPU profile: model `medium`, device `cpu`, compute type `int8`, Portuguese, optional diarization, JSON output and 6 threads. The thread count is only a known working reference configuration.

## AMD GPU path: core components

| Component | Role | How it is obtained | Reproducibility status |
| --- | --- | --- | --- |
| FFmpeg | Decode input to 16 kHz mono WAV | Upstream FFmpeg / trusted package source | Exact executable hash pending |
| whisper.cpp | Native ASR executable built with Vulkan | [ggerganov/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Source commit and build commands not yet locked |
| Vulkan-capable graphics driver/toolchain | AMD inference backend for whisper.cpp | GPU vendor/Windows | Driver/tool versions pending |
| Whisper `large-v3` GGML model | ASR weights | Author-approved upstream distribution | Source, size and SHA-256 pending |
| Python (main environment) | Orchestrator | Official Python distribution | Version pending |
| `torch`, `whisperx`, `numpy`, `pandas` | Local alignment integration, audio processing, speaker assignment | Python packages | Package versions pending |
| `onnxruntime-directml` | DirectML ONNX inference | Python package | Version and provider audit pending |
| Portuguese wav2vec2/CTC ONNX + vocab | Word alignment | Exported/acquired from an authorized model | Export recipe, model revision and hashes pending |
| pyannote Community-1 ONNX segmentation/embedding | Speaker diarization | Subject to model terms and authorized acquisition | Export provenance and hashes pending |
| External `onnx_pyannote.py` integration | Community-1 model invocation | Third-party source | Exact repository, commit and redistribution terms pending |
| `alinhamento_directml*.py` | Alignment adapter/worker | Local project source | Sanitized public package pending |
| `diarizacao_directml_worker.py` | Diarization worker | Local project source | Sanitized public package pending |
| `preload_alinhamento.py` | CTC warmup | Local project source | Sanitized public package pending |

Do not install a made-up `requirements.txt` or download models from arbitrary mirrors. We will publish locked manifests only after verifying the actual installed versions and checksums.

## Runtime boundaries actually observed

- The main app first verifies input, models, FFmpeg and worker resource paths.
- It calls whisper.cpp with Vulkan device index 0, `-mc 0`, `-bs 1`, JSON output and a user-configurable thread count.
- It validates DirectML evidence from alignment/diarization workers; some ONNX operations run on CPU by design.
- On Windows, FFmpeg/TorchCodec dynamic library discovery was a development issue; a localized runtime DLL-directory fix resolved a warning on the reference PC. That local modification is **not** a generic install step without a reproducible diagnosis.
- Separate Python environments must not install or overwrite the user's independently working CPU environment.

## Information still required for exact reproduction

1. `python --version` for each isolated environment.
2. Relevant package versions / `pip freeze` for **each** environment, reviewed for local paths and secrets.
3. FFmpeg and whisper.cpp versions, source revisions and build settings.
4. Vulkan SDK/toolchain and AMD driver version (if installed / required for that build).
5. SHA-256 and acquisition links for each downloaded/exported model.
6. Provenance and license for the external ONNX Community-1 integration.
7. Accepted pyannote / Hugging Face access terms, without embedding credentials.
8. Reproduction results on a clean Windows installation and at least one non-reference device.

Version pinning is not the same as model licensing: package wheels, scripts, exported model weights and recordings have different distribution rules. See [reproducibility](REPRODUCIBILITY.md) and [release criteria](RELEASE_CRITERIA.md).
