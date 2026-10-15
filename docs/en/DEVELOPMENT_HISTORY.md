# Development history and verified learning

This is a **technical reconstruction** from local patches, integrated logs and tests, not a verbatim meeting diary. Dates and timings are given only when supported by recorded outputs.

## 1 — Local CPU transcription

A functioning Windows/PowerShell WhisperX workflow existed first. Its reference settings used the `medium` model, CPU `int8`, Portuguese, optional pyannote diarization and machine-readable JSON. The original CPU setup was explicitly preserved during GPU experimentation.

**Lesson:** use isolated Python environments and keep a tested fallback until the accelerated path has passed end-to-end validation.

## 2 — Exploring AMD recognition backends

Because the reference GPU had no CUDA support, experimentation moved to **whisper.cpp compiled for Vulkan**, initially with `medium` and subsequently `large-v3`. Source media were converted to PCM 16 kHz mono with FFmpeg. JSON from whisper.cpp was parsed into segment timestamps and text before alignment.

**Lesson:** ASR recognition alone is not the whole WhisperX workflow; word-level alignment and diarization require additional components.

## 3 — First ONNX/DirectML integration

Speaker diarization was moved to a Community-1 ONNX worker. Recognition ran through Vulkan; initially, some other processing remained CPU-bound. Isolated worker environments reduced dependency conflicts.

**Lesson:** a high GPU-utilization graph proves activity, not automatically that **every** model stage used the GPU. Capture backend/provider evidence separately.

## 4 — Portuguese CTC word alignment on DirectML

A Portuguese wav2vec2 CTC model was exported/acquired as ONNX with its vocabulary and called through a separate worker. Development QA compared the results against WhisperX alignment and confirmed real DirectML operators.

**Lesson:** alignment scores indicate timing uncertainty, **not** confidence that a recognized word is linguistically correct. The pipeline was limited to Portuguese alignment rather than silently running an untested language.

## 5 — Speaker overlap and exclusive diarization

A practical overlap revealed mixed word attribution. The regular diarization tracks were retained as evidence; **exclusive diarization** was used for the actual word-to-speaker assignment.

**Lesson:** do not erase genuine overlap just to obtain clean speaker labels. A voice ID is not proof of a person's identity.

## 6 — CTC warmup

Import and setup overhead for WhisperX alignment was reduced by starting a **synthetic preload in a background thread while whisper.cpp performed ASR**. The thread is joined before real alignment to prevent unsafe concurrent use.

Observed three-minute sample: **110.78 s without preload → 101.03 s with preload**, preserving the 214 words, scores, timestamps and speaker labels reported in the comparison. The 9.75-second improvement is approximately **8.8% relative to the same GPU pipeline**, not a CPU-vs-GPU comparison.

**Lesson:** optimize startup only when content/attribution parity is maintained.

## 7 — End-to-end long recording

A 1,080.45-second media file completed in **448.93 seconds**: ASR 297.16 s, alignment 90.11 s, diarization 53.28 s. The run produced 326 raw ASR segments, 333 integrated segments, 1,805 aligned words and 67 diarization overlap detections.

Four alignment segments emitted a backtrack warning and fell back to original segment timing. The pipeline still reported alignment and diarization as completed.

**Lesson:** a completed run can still contain uncertain words/timestamps; warnings are evidence for review, not automatic reason to fabricate corrected text.

## 8 — Simpler output profiles

Early development produced five files per run for troubleshooting. The user-facing contract was simplified:

- **Normal**: integrated JSON only.
- **Quality**: integrated JSON plus QA findings.
- **Debug**: all five outputs.

After simulated regression tests, the **Normal** profile was run on a real 25-second sample with the AMD GPU. It generated 11 segments, 47 aligned words and exactly one integrated JSON file. The other profiles still await post-change hardware regression.

**Lesson:** keep debugging visibility available while making routine transcription simple.

## 9 — Public documentation and reproducibility

The locally working implementation is not the same as a reproducible public release. The next milestones are source provenance, safe dependencies, licensing, clean installs, realistic samples, screenshots and accessible step-by-step guides.

**Lesson:** share verified knowledge now; label unverified distribution steps clearly until they are tested.
