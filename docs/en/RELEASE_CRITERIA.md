# Release status and acceptance criteria

## Two different milestones

| Milestone | Current status |
| --- | --- |
| **Local AMD application v1.0.0** | Full 18-minute integration passed; Normal profile short AMD regression passed |
| **Public N3LX Transcription Toolkit v1.0.0** | **Not released**: setup/source packaging and reproduction are incomplete |

A GitHub repository containing documentation is not a downloadable software release. Do not tag a v1.0.0 software version prematurely.

## Public software release gates

- [ ] Decide and publish license(s) for original project code and documentation.
- [ ] Inspect every bundled source file and installer for secrets, private identity, client data and third-party intellectual property.
- [ ] Establish third-party provenance and permitted redistribution (whisper.cpp, WhisperX, ONNX integration, model exports and weights).
- [ ] Pin exact dependency versions **separately** for CPU, main GPU and DirectML environments.
- [ ] Pin/reproduce the whisper.cpp Vulkan build, model acquisition and model hashes.
- [ ] Provide an accessible CPU install from a clean Windows environment.
- [ ] Provide an AMD GPU install from a clean compatible Windows environment.
- [ ] Validate Vulkan/DirectML execution evidence and a clear fail/diagnostic policy.
- [ ] Revalidate Normal, Quality and Debug output profiles on real hardware.
- [ ] Test at least one short and one long synthetic or authorized public media asset.
- [ ] Validate missing model, absent FFmpeg, device mismatch, permission errors and partial-failure behavior.
- [ ] Document expected disk/RAM/VRAM estimates based on measurements (not guesses).
- [ ] Publish sanitized screenshots, alt text and nonconfidential examples.
- [ ] Add installation rollback and dependency update procedures.
- [ ] Publish the release changelog and a Git tag only after verification.

## Version policy

- Use [Semantic Versioning](https://semver.org/) for publicly distributed software, beginning only when a supported installation is ready.
- Use [Conventional Commits](https://www.conventionalcommits.org/) in English throughout development.
- Treat the local v1.0.0 implementation as a **reference state**; a later public release might require packaging changes and should not pretend to be byte-identical.

## Known risks

- Technical: GPU and driver variations, ONNX export provenance, dynamic-library discovery, model compatibility and errors under degraded/overlapping audio.
- Process: misleading installation claims, unsupported precision claims, and accidental release of sensitive media or tokens.
- Legal/license: model terms and upstream code licenses require independent verification.

Ownership of these outstanding tasks remains with this repository; the related operating framework is a **motivating use case**, not a home for this Toolkit's change history.
