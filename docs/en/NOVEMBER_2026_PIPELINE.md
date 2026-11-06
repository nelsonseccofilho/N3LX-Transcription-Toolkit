# November 2026 reference: offline AMD GPU pipeline, unified QA, progress and evidence delivery

> **Status:** validated on one Windows reference machine. Developer-preview first-party sources are now in this repository, but there is no complete public installer, exact validated diarization worker, downloaded model distribution or clean-machine QA. This is a later local `NELX-Whisper-GPU` workflow and **does not replace the separate v1.0.0 local CLI** described in the existing documentation.

## Architecture and reference configuration

| Step | Local component | Verification |
| --- | --- | --- |
| Extract | FFmpeg, mono PCM 16 kHz | Source duration and converted WAV |
| Recognize | whisper.cpp, **Whisper large-v3**, Vulkan on AMD Radeon RX 6600M | Vulkan observed in engine log |
| Decode | Portuguese (`-l pt`), 6 threads, GPU 0, `-mc 0`, **`-bs 5`** | Exact process profile recorded |
| Word timing | Portuguese wav2vec2 XLSR-53 CTC exported to ONNX via DirectML | Forced alignment, not just a logit check |
| Speakers | pyannote Community-1 ONNX/DirectML | Regular and exclusive turns |
| Integrate | Python word timestamps + exclusive speaker attribution | Integrated JSON and warnings |
| Deliver | Private framework evidence adapter | **One `<source-file>.framework.json` per recording** |

GPU execution is backend-specific. The ASR stage uses Vulkan; alignment and diarization use ONNX Runtime DirectML. Some auxiliary ONNX CPU operators are expected, but full unintended CPU fallback must be identified from execution evidence. Keep isolated Python environments for inference, model export and optional CPU fallback; avoid incompatible dependency upgrades across them.

The previous baseline used `-bs 1`; the later local profile uses `-bs 5` for a wider decoder search. A backup and separate cache signature were created. **There is no controlled human-reviewed WER comparison proving `-bs 5` is more accurate.**

## Operator commands — local Git Bash only

~~~bash
# These shell functions exist ONLY after being configured on the reference PC.
transcrever recording.mkv           # one recording
transcrever_pasta                   # current directory, sequential
transcrever_pasta "/path/to/media"  # specified directory
~~~

The wrapper checks `.mkv`, `.mp4`, `.mp3`, `.ogg` extensions and passes compatible input to FFmpeg. **MKV has real end-to-end test coverage in this iteration**; the other extensions still require individual format regression. Folder processing is non-recursive, one source at a time, with per-file outcomes. Git Bash Tab completion works with escaped spaces after correct relative-path normalization. `transcrever_pasta` expects a directory, not a filename. The previous PowerShell 7 `whisperxgpu` examples remain historical/local; the Git Bash wrapper is now supplied as source, but cloning this repository does not automatically install either interface or their external GPU dependencies.

## The six-stage resumable QA

1. `preflight`: model paths, engine and FFmpeg.
2. `audio_16khz`: conversion and media duration.
3. `ctc_directml`: DirectML provider/operator and 2/3-second logit equivalence (**not word alignment**).
4. `asr_vulkan`: segment transcription and Vulkan backend confirmation.
5. `diarization_directml`: Community-1 regular/exclusive intervals and DirectML evidence.
6. `integracao_final`: CTC forced word timing and word-to-speaker attribution.

Each stage can be PASS/FAIL/PENDING. Cached PASS results may be reused **only** while source, code, models and relevant decoder settings match the cache fingerprint. Separating the `-bs 5` cache from `-bs 1` avoids stale ASR reuse. Do not repeatedly rerun completed components solely to check whether a downstream stage succeeded. A full `QA_END_TO_END_PASS` was observed after the missing final integration was added.

### Sanitized anonymous 21-minute MKV test

| Observed metric | Result |
| --- | ---: |
| Source duration | 1,262.891 s |
| Sum of recorded stage times | about 784 s / 13min04s |
| ASR/Vulkan | 562.92 s; 530 segments |
| Diarization/DirectML | 61.86 s; 477 regular / 487 exclusive turns |
| Integration | 133.19 s; 530 segments |
| Word tokens / aligned | 3,202 / 3,149 = **98.34% timing coverage** |
| Aligned words with speaker | 3,146 / 3,149 = **99.90% automatic coverage** |
| End-to-end result | **6/6 PASS** |

These are local stage metrics (about 1.61× media-duration throughput in this run), **not** a CPU-vs-GPU speedup or a matched comparison to the earlier benchmark. Integration reported both DirectML and auxiliary CPU operators. Numerals and very short audio windows can remain without aligned timestamps. **98.34% alignment coverage is not 98.34% textual correctness or measured WER.** Speaker labels are anonymous and may be wrong or mixed inside a segment; a human must review consequential excerpts against the source recording.

## Real-time progress and truthful reporting

A read-only monitor was first tested in a second Git Bash window, then integrated into the `transcrever` and `transcrever_pasta` wrappers. During an active MKV transcription it displayed **3/6 stages PASS, ASR running and 11.4% of the audio processed**. ASR percentages are based on actual engine-log timestamps. Other stages must show running/pending instead of invented percent or ETA. The old runner printed only stage completion, which could look frozen during long ASR work.

## One JSON for framework ingestion

The newer routine wrapper delivers **one `<original-filename>.framework.json`** into the input-adjacent `transcricao/` folder; intermediate audio, QA reports and cache remain in a separate private workspace.

Expected adapter semantics: stable Evidence ID, origin fingerprint/provenance, language/profile, original ASR text, stable timestamped segments, anonymous speaker attribution, review warnings and `UNREVIEWED` review state. Mixed word-level speakers must not be silently flattened into an asserted identity. Bounded time windows may index segments without duplicating their text. The exact exported field schema has **not** yet been verified as a public stable JSON Schema; see [adapter contract](FRAMEWORK_EVIDENCE_ADAPTER.md).

The [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system/blob/main/docs/EVIDENCE_INGESTION.md) distinguishes **primary recording → derived transcript → reviewed evidence → requirement/decision → implementation/QA**. A transcript is not an automatically approved requirement. Client recordings, transcripts, private file paths, tokens and QA logs must not be committed to the public Toolkit.

## Lessons and remaining gates

- Vulkan and DirectML must be verified independently; ONNX CPU helper operators are not a blanket failure.
- Isolate export, inference and CPU fallback environments; pin source revisions and model terms before distribution.
- Use one resumable executor rather than repeated micro-tests; preserve PASS evidence and expose failures.
- Cache keys must change when decoder settings, model artifacts or relevant code change.
- Preserve word/segment timing disagreement and diarization ambiguity for human review.
- Show only measured progress, and keep technical evidence separate from the user's one-file deliverable.
- No public software release until license/provenance review, sanitized sources and dependency locks, clean Windows install, all input formats and batch interruption testing, synthetic schema fixtures and human-reviewed text accuracy benchmarks.

See [release criteria](RELEASE_CRITERIA.md), [validation](VALIDATION.md), [dependencies](DEPENDENCIES.md) and [earlier CLI reference](OUTPUTS_AND_CLI.md).

## Source layout published as developer preview

The source now includes [QA](../../src/n3lx_toolkit/qa_unificado.py), [monitor](../../src/n3lx_toolkit/monitor.py), [one-JSON exporter](../../src/n3lx_toolkit/export_framework.py), [Git Bash wrapper](../../scripts/gitbash_commands.sh) and [synthetic tests](../../tests/test_toolkit.py). The exact Windows-validated diarization worker is **not** silently replaced by a different source; it must be supplied as an external prerequisite. The published runner is therefore a developer candidate rather than a new hardware-verified release.

[Developer setup](LOCAL_DEVELOPER_SETUP.md) · [Release gates](RELEASE_CRITERIA.md)
