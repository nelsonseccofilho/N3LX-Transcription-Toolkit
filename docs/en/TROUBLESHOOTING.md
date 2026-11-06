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

## Git Bash and November 2026 local workflow

| Symptom | First check |
| --- | --- |
| `transcrever: command not found` | Ensure the **local** Bash function was installed/sourced; the public clone does not install it. |
| Relative name containing spaces | Use Tab completion or quoting and normalize to an absolute input path before export. |
| `transcrever_pasta` called with a file | This accepts a directory; use `transcrever` for one file. |
| `~/.bashrc` startup warning | Git Bash may create `~/.bash_profile` to load `~/.bashrc`; verify functions in a fresh login shell. |
| Silence during `asr_vulkan` | An older QA runner logged subprocess output without a dashboard. The newer monitor reads actual ASR timestamps; silence alone does not prove a hang. |
| Monitor installed but raw logs still appear | Installing the read-only viewer is different from wiring the wrapper to the progress runner. |
| Cache reports reused results after Beam Size change | Check code/model/settings-sensitive cache keys. Never reuse `-bs 1` output as a `-bs 5` validation. |
| Segment-level speaker conflicts with word labels | Preserve speaker uncertainty for review; do not silently replace word-level evidence. |
| Numeric words or very short CTC windows unaligned | Retain original text with an explicit warning; do not fabricate timestamps. |

Never paste unredacted private paths, recordings, transcripts, tokens or raw processing logs into public issues.

## Developer-preview missing worker

A cloned source tree without the exact local Community-1 diarization worker and authorized ONNX models is incomplete. Set N3LX_DIARIZATION_WORKER to the verified local worker path or preserve the already working local QA via N3LX_QA_SCRIPT. These are recovery/compatibility overrides, **not** a substitute for model rights, licensed acquisition or clean-machine validation. See [developer setup](LOCAL_DEVELOPER_SETUP.md).
