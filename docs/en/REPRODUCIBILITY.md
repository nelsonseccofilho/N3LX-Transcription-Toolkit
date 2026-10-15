# Reproducibility plan

A working local machine is only the starting point. A public installation guide is ready when a new Windows user can follow it from a clean environment **without copying private state**.

## Stage A — machine and software inventory

Collect, review and version:

1. Windows version and hardware capability (without machine or user identity).
2. Python versions for each virtual environment.
3. `pip freeze` or locked package manifests for the CPU, main GPU and DirectML worker environments separately.
4. FFmpeg, compiler/build system, Vulkan and whisper.cpp versions/commits.
5. AMD graphics driver information and ONNX Runtime execution providers.
6. Model names, upstream license/access terms, original source revision and SHA-256.
7. Actual entry-point registration used by `whisperxgpu`, without home-directory paths or embedded credentials.

Never commit `pip freeze` containing secrets, tokens, private wheel URLs or identifiable absolute paths. Redact before sharing.

## Stage B — package only authorized artifacts

- Review first-party source for credentials, personal paths, unused code and unlicensed third-party fragments.
- Keep large downloaded weights **outside Git**; provide authorized download/export recipes and hash checks.
- Pin exact third-party revisions; record license requirements separately from dependency versions.
- Treat optional diarization access as an explicit, consent-aware setup step.
- Use separate environments for CPU and GPU/DirectML stages.

## Stage C — clean-machine reproducibility

On a fresh Windows environment with compatible hardware:

1. Install prerequisites and reboot only if needed.
2. Install the **CPU** profile and validate a public/synthetic short sample.
3. Install the **AMD GPU** profile independently.
4. Confirm the actual Vulkan device and DirectML ONNX providers.
5. Validate ASR, alignment, speaker diarization and output profiles.
6. Verify GPU failure behavior and no silent replacement of intended neural stages by CPU inference.
7. Repeat a longer run; publish timings and memory usage with hardware details.
8. Uninstall/reinstall; confirm there is no dependency on developer-specific paths.

## Stage D — publication

After audit, create a signed/tagged release candidate with a versioned dependency manifest, changelog, license files, test evidence and reproducible setup steps. Preserve a rollback procedure. Do not announce a public v1.0.0 release before this gate.

See [release criteria](RELEASE_CRITERIA.md) for explicit blockers.
