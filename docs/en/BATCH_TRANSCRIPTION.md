# Batch transcription on Windows (PowerShell 7)

**Status:** commands used in the local AMD GPU v1.0 workflow. The batch loop was observed starting correctly on a real folder containing seven MKV files. Completion of that entire seven-file batch has not yet been independently verified. **This is not a native batch mode inside `whisperxgpu`.** The GPU application is currently installed only on the reference Windows machine; the public repository does not yet include its installer.

## Before running

1. Open **PowerShell 7** in the folder containing your media files.
2. Make sure the existing local `whisperxgpu` command is available and that its Vulkan/DirectML dependencies have already been installed and validated.
3. Keep enough free disk space for the temporary audio and results; prevent Windows from sleeping during long unattended runs.

## One media file — canonical reference command

```powershell
whisperxgpu ".\FILENAME.mkv" --model large-v3 --device vulkan --diarize --output_dir ".\transcricoes\" --output_format json --language pt --threads 6
```

This uses Whisper **large-v3** ASR via Vulkan, alignment/diarization via DirectML, Portuguese, six CPU helper threads and the default **Normal** output profile. It saves an `*.integrado.json` file in `./transcricoes/`. You can replace `FILENAME.mkv` with a real filename.

## Every MKV in the current folder — canonical PowerShell loop

```powershell
Get-ChildItem -File -Filter *.mkv | Sort-Object Name | ForEach-Object { Write-Host "`nTRANSCREVENDO: $($_.Name)" -ForegroundColor Cyan; whisperxgpu $_.FullName --model large-v3 --device vulkan --diarize --output_dir ".\transcricoes" --output_format json --language pt --threads 6; if ($LASTEXITCODE -ne 0) { Write-Warning "Falha ao transcrever: $($_.Name)" } }
```

### Exactly what it does

- Finds `*.mkv` files in **only the current folder**; it does **not** search subfolders.
- Sorts files by name, processes **one at a time** and prints the filename before each run.
- Calls the same GPU transcription pipeline with the same model, diarization, output format, language and thread count.
- Writes integrated JSON outputs under `./transcricoes/`; with the current default Normal profile no extra QA/debug outputs are retained.
- Warns when an individual command returns a nonzero exit code; the `ForEach-Object` loop then moves to the next input.

### Important boundaries

- **No automatic skip/resume:** running the loop again will process every matching file again, even if a transcript already exists. The timestamped output pattern can create additional results.
- **Not a filesystem monitor:** files added after the command starts are not promised to be included.
- **Not an unattended job service:** keep PowerShell and Windows running; a closed terminal or PC suspension interrupts processing.
- **No overall success report:** the example prints each filename and warnings; review the terminal and outputs to verify the whole batch.
- **Only MKV:** other FFmpeg-readable formats must be selected with a different PowerShell filter; do not assume the given command automatically handles MP3/MP4.
- **Avoid joined commands:** paste **one full command at a time**. Combining a one-file command and the loop without separation can produce an invalid argument such as `--threads 6Get-ChildItem`.

## Example result layout

```text
recording-folder/
├── meeting-01.mkv
├── meeting-02.mkv
└── transcricoes/
    ├── meeting-01.gpu-large-v3.TIMESTAMP.integrado.json
    └── meeting-02.gpu-large-v3.TIMESTAMP.integrado.json
```

The exact timestamp depends on the run. Results and logs for private recordings should stay outside public Git.

## Next planned improvement

Native batch support with reliable resume/skip handling, collision prevention, per-file outcomes and progress summary is a future feature—not part of the locally validated v1.0 CLI.

See also [CLI/output contract](OUTPUTS_AND_CLI.md), [validation](VALIDATION.md) and [AMD setup](AMD_GPU_SETUP.md).
