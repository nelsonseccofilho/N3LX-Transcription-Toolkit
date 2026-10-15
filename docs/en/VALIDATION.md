# Validation, quality and limitations

## Local reference evidence

Hardware: Windows 11 Pro, AMD Radeon RX 6600M 8 GB. The values below come from the author's local application output, not an independent multi-device benchmark.

| Metric | 18-minute reference run |
| --- | ---: |
| Media duration | 1,080.45 seconds |
| Total processing time | 448.93 seconds |
| ASR processing | 297.16 seconds |
| Alignment processing | 90.11 seconds |
| Diarization processing | 53.28 seconds |
| Recognized ASR segments | 326 |
| Integrated segments | 333 |
| Aligned words | 1,805 |
| Regular / exclusive speaker intervals | 388 / 368 |
| Detected voice overlaps | 67 |
| QA review alerts | 320 |

**Backends:** Vulkan confirmed for large-v3 speech recognition; DirectML confirmed for ONNX alignment and diarization. The 448.93 s total is about 2.4 times faster than media duration. It is **not** a CPU-to-GPU speedup estimate.

Four segments reported word-alignment backtrack warnings and used the original segment timing where necessary. Both alignment and diarization finished with an `ok` stage status.

## Output profiles in the local reference app

| Profile | Persisted outputs | Regression status |
| --- | --- | --- |
| Normal (default) | `integrado.json` | Verified with a 25-second real AMD GPU run: 11 segments, 47 aligned words |
| Quality | Integrated + `qualidade.json` | Covered by simulated tests; fresh real-device profile regression pending |
| Debug | Integrated + quality + raw ASR + diarization + processing log | Covered by simulated tests; fresh real-device profile regression pending |

The reference machine's application sources and installers are **not yet included** in this public repository.

## Interpreting the QA report

The alignment `score` is about **word timing alignment**, not a calibrated probability that Whisper heard the right word.

- A low alignment score does not automatically mean a transcription error.
- A high score does not prove the recognized word is correct.
- Speaker identities such as `SPEAKER_00` are **anonymous clustering labels** until someone checks the original audio.
- Overlapping speakers and low-quality calls can lead to missing or incorrect words.
- A QA alert count is **not** a word error rate (WER).

Do not silently invent missing words or force uncertain speaker labels.

## What release-quality tests still need to cover

- Independent clean-install verification of both supported paths.
- Equivalent CPU vs AMD GPU benchmark on the same input and comparable settings.
- Human-reviewed transcript accuracy against a reference transcript.
- Long-run behavior, interrupted jobs, insufficient memory, and invalid media.
- Output contract tests for all profiles, languages and optional diarization.
- License/security review before publishing installers or model distribution.

Preserve the original media to review consequential decisions and timestamps. Never publish sensitive meeting material as test data.
