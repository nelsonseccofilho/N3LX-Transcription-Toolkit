# Troubleshooting — starter guide

**This guide records known categories of problems.** Exact error remediation and package-version pinning must be verified against the public release package before being presented as universal fixes.

| Symptom | What to check first |
| --- | --- |
| FFmpeg not found | Verify `ffmpeg -version` in the **same terminal** used to run transcription |
| CPU task unexpectedly slow | Model size, available RAM, number of threads, and whether the requested profile is CPU |
| WhisperX Python package errors | Supported Python/PyTorch versions in current upstream documentation and an isolated virtual environment |
| Diarization is denied or fails to download | Model license/terms, Hugging Face account/token and network access |
| AMD GPU activity is absent | Vulkan detection, selected device, driver, model log and DirectML provider evidence |
| ONNX runs using unexpected CPU operations | Distinguish legitimate auxiliary CPU operations from a complete CPU model fallback |
| Word alignment backtrack warning | Compare the original segment timestamps and listen to that region; do not invent new words |
| Odd speaker assignments | Listen to original overlapping speech, compare regular and exclusive intervals |
| Unexpected extra files | Check output profile: Normal, Quality or Debug (local reference app only) |
| Wrong or invented words | Inspect original audio quality, background noise and overlapping speakers; model scores do not confirm text accuracy |

## Good bug reports

Include your OS, CPU/GPU model, relevant dependency versions, *sanitized* terminal output, a reproducible public or synthetic media sample, exact command (without secrets), and expected vs observed behavior.

**Never post** tokens, real client recordings, private meeting transcripts, personal directory paths or unredacted screenshots.

If the problem is specific to upstream WhisperX, whisper.cpp, ONNX Runtime or pyannote, verify whether it reproduces in that upstream project before filing a toolkit-specific issue.
