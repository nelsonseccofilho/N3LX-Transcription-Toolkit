# Why this project exists

## The original constraint

The author was already transcribing recorded media locally using **WhisperX on CPU**. That worked, but longer sessions took time, and the author wanted to accelerate processing without leaving local hardware.

Many popular GPU setup guides assume access to an NVIDIA graphics card and its CUDA software stack. The available machine instead had an **AMD Radeon RX 6600M with 8 GB of VRAM**.

The practical engineering question became:

> Can we keep local transcription, word-level timestamps and speaker diarization while accelerating the heavy inference stages on a consumer AMD GPU, without CUDA?

The result was a gradually assembled, tested pipeline that uses Vulkan where whisper.cpp provides the ASR backend and DirectML for the exported ONNX alignment and diarization models.

## Connection to the operating framework

This tool was created to support [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system), a versioned, evidence-driven workflow for long-running AI-assisted product and design engineering work.

The framework needs an optional way to transform authorized meeting recordings into machine-readable evidence that can be reviewed and mapped to decisions. Its operating principle is:

- Original recording is not the transcript.
- Transcript is not an approved requirement.
- Approved requirement is not implementation.
- Implementation is not verified completion.

The Toolkit addresses the **recording → searchable transcript** part. It does not make business decisions, approve requirements or replace the source media.

The operating framework is one use case, **not** a runtime dependency. The Toolkit can also help with lectures, authorized interviews and personal archives.

## Design goals

1. **No mandatory CUDA**: provide a CPU path and a documented AMD GPU path.
2. **Local-first**: media does not need to be uploaded to a hosted transcription API.
3. **Reproducible**: track exact components, versions, assumptions and known failures.
4. **Transparent**: report which backend ran; do not hide uncertainty.
5. **Reviewable**: preserve timestamps and flag low-confidence alignment or speaker overlap.
6. **Accessible**: document the method for readers with different levels of technical experience.
7. **Safe by default**: keep private audio, model credentials and local identity data out of public Git.

## What is established vs what is not

The local pipeline works on the AMD reference machine and a complete 18-minute processing test passed. The evidence does **not** show that it runs on every AMD GPU, is universally faster than CPU, or transcribes every word correctly.

Public clean-install packaging is a separate engineering milestone from the validated local prototype. Until that milestone is met, the public repository is documentation-first.
