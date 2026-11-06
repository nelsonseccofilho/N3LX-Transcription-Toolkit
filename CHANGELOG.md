# Changelog

All notable changes are tracked using [Conventional Commits](https://www.conventionalcommits.org/).

**Public status: developer-preview sources and documentation; no complete public installer.** The local reference application's v1.0.0 validation is not a public release or public installer.

## Unreleased

### Documentation
- Document the canonical single-media and sequential MKV batch commands tested on the local AMD GPU reference, with limitations and PowerShell troubleshooting.
- Document why the Toolkit was created to support [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system), and the AMD/no-CUDA motivation.
- Publish reference hardware and explicitly distinguish media throughput from CPU/GPU speedup.
- Explain GPU stage boundaries, Python environment isolation and dependencies.
- Consolidate engineering history, CLI/output contracts, validation and reproduction gates.
- Provide an English-first README, a Brazilian Portuguese entry point, CPU setup and troubleshooting.
- Establish security, contributing, ignore-file and public release requirements.

### November 2026 local reference — source preview, not a release

- Capture a distinct AMD GPU local runner: Whisper large-v3/Vulkan `-bs 5`, Portuguese CTC word alignment and Community-1 ONNX/DirectML speaker diarization.
- Record six-stage resumable QA, parameter-aware cache, end-to-end PASS and sanitized metrics from an anonymous 21-minute recording.
- Document Git Bash single-file/sequential folder commands and a live progress dashboard based on real ASR timestamps.
- Document one framework-oriented JSON per recording, private QA evidence separation and human-review authority boundaries.
- Add bilingual guides and release blockers; publish recovered first-party QA, monitor, exporter and Git Bash wrapper sources plus synthetic tests. **No client media, model weights, external worker or installer is published**.

### Pending
- Review/publish project and third-party licenses.
- Audit and publish dependency locks, authorized model acquisition, installation scripts and source.
- Pass independent clean-install checks, integration QA and accessible documentation review before a public software release.

### Recovery cycle: Community-1 worker interface (developer preview)

- Recover an earlier DirectML first-party diarization worker and adapt it to provide regular and **exclusive** Community-1 speaker intervals.
- Add mandatory exclusive non-overlap checking and model-path configuration; preserve DML provider/operator checks.
- Fingerprint diarization ONNX and PLDA assets in the QA cache signature.
- Add mocked worker/QA contract tests; **no independent GPU run, installer release or client data published**.
