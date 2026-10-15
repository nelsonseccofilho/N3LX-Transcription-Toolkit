# Contributing

Thank you for helping make local transcription more reproducible and accessible.

## Project stage

Documentation is available first; public installers and application source will be added only after provenance, dependency, licensing and clean-machine checks. Avoid presenting an unverified configuration as officially supported.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) in **English**:

```text
docs(readme): explain setup status
docs(cpu): clarify Windows prerequisites
feat(amd-gpu): add verified Vulkan installation script
fix(diarization): preserve exclusive speaker mapping
test(outputs): validate normal profile on AMD
chore(deps): pin tested ONNX Runtime versions
```

Preferred types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.

Each change should document what was tested, on what OS/hardware, and what is still unverified. Keep CPU and AMD GPU installation paths isolated. Prefer scoped pull requests rather than unrelated changes bundled together.

## Documentation and accessibility

- Write technical source and primary README in English.
- Include Portuguese (Brazil) guidance for beginner-facing flows.
- Use commands that can be copied, explain prerequisites, and distinguish verified instructions from proposals.
- Describe screenshots with useful alt text; only include redacted, permission-cleared images.

## Data and secrets

Use non-sensitive synthetic samples. Do not commit original meeting recordings, confidential transcripts, model access tokens, absolute user-specific paths or model weights with unclear redistribution terms.

Please review [SECURITY.md](SECURITY.md). The project's own software license is pending; contribution licensing terms must be clarified before accepting substantive code contributions.
