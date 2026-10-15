# CPU setup — Windows

**Status:** guide based on the upstream WhisperX workflow; installation on a fresh independent machine is not yet a project release test.

This is the simpler starting point when you do not have a supported GPU. The CPU environment must remain **separate** from any AMD GPU environment.

## Prerequisites

- Windows and PowerShell 7 (recommended for these examples).
- Python compatible with the **current** WhisperX release.
- FFmpeg accessible from the terminal.
- Sufficient disk space and RAM for downloaded models.

Confirm Python and FFmpeg are available:

```powershell
python --version
ffmpeg -version
```

WhisperX dependencies can change. Check the [upstream WhisperX repository](https://github.com/m-bain/whisperX) before selecting a Python/PyTorch combination.

## Isolated environment

Create a dedicated project directory, and from inside it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install whisperx
whisperx --help
```

These commands are a starting point, **not** a locked, clean-machine-tested installer for this repository.

## Example transcription

```powershell
whisperx ".\meeting.mkv" --model medium --device cpu --compute_type int8 --diarize --output_dir ".\transcriptions" --output_format json --language pt --threads 6
```

If diarization is enabled, pyannote models may require a Hugging Face account, acceptance of model terms and a read token. Consult the current upstream instructions. Store secrets securely; never paste tokens into public issues, scripts or commits.

CPU speed depends heavily on processor, recording duration, model and thread count. The `--threads 6` value is an **example**, not a universal optimum.

## Expected result

Inspect the JSON in `transcriptions/`. Check that text, segments, timestamps and (when enabled) speaker data exist. Listen to a few random portions of the source recording before trusting the text.

If installation or diarization fails, start with [troubleshooting](TROUBLESHOOTING.md).
