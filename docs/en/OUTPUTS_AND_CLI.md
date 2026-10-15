# CLI and output contract — local AMD reference

**Applicability:** currently configured local GPU application. The public repository does not yet distribute this CLI.

## Example commands

```powershell
# Routine transcription (default Normal output profile)
whisperxgpu ".\recording.mkv" --model large-v3 --device vulkan --language pt --diarize

# Keep a separate QA report
whisperxgpu ".\recording.mkv" --output-profile quality

# Keep all processing evidence for debugging
whisperxgpu ".\recording.mkv" --output-profile debug

# Disable diarization
whisperxgpu ".\recording.mkv" --no-diarize

# Disable the CTC warmup experiment
whisperxgpu ".\recording.mkv" --no-preload-align
```

## Single-file and batch commands actually used in PowerShell 7

The following commands are supported by the currently configured **local AMD GPU application**. A fresh clone of this documentation-only repository does not install `whisperxgpu`.

**Single file:**

```powershell
whisperxgpu ".\FILENAME.mkv" --model large-v3 --device vulkan --diarize --output_dir ".\transcricoes\" --output_format json --language pt --threads 6
```

**All `*.mkv` files in the current directory (sequential):**

```powershell
Get-ChildItem -File -Filter *.mkv | Sort-Object Name | ForEach-Object { Write-Host "`nTRANSCREVENDO: $($_.Name)" -ForegroundColor Cyan; whisperxgpu $_.FullName --model large-v3 --device vulkan --diarize --output_dir ".\transcricoes" --output_format json --language pt --threads 6; if ($LASTEXITCODE -ne 0) { Write-Warning "Falha ao transcrever: $($_.Name)" } }
```

This loop is a PowerShell wrapper, not an implemented native wildcard/batch feature in the application. It does not recurse into folders or skip previously processed recordings. It prints a warning for each nonzero exit code and then continues; it does not provide a final aggregate report. Paste either example separately: joining both commands can accidentally pass `6Get-ChildItem` as the thread value.

See [batch transcription guide](BATCH_TRANSCRIPTION.md) for prerequisites, edge cases, and output examples.
## Flags confirmed in the v1.0.0 local script

| Argument | Default | Notes |
| --- | --- | --- |
| `arquivo` | Required | Input media readable by FFmpeg |
| `--model` | `large-v3` | Supported choices: `large-v3`, `medium`; local weights needed |
| `--device` | `vulkan` | Only accepted GPU ASR backend in this script |
| `--language` | `pt` | Other languages not validated for ONNX/DirectML word alignment and rejected |
| `--threads` | `6` | CPU helper and whisper.cpp thread count |
| `--gpu` | `0` | Vulkan device index |
| `--diarize` / `--no-diarize` | Enabled | Optional speaker attribution |
| `--output_dir` | Input-adjacent `transcricoes` | Target folder |
| `--output_format` | `json` | Only JSON supported in local GPU app |
| `--output-profile` | `normal` | `normal` / `quality` / `debug` |
| `--experimental-preload-align` / `--no-preload-align` | Enabled | Synthetic CPU CTC preload |
| `--low-score` | `0.20` | QA threshold for low word alignment score |
| `--long-segment` | `15.0` | QA duration threshold in seconds |
| `--whisper-cli` | Local whisper.cpp executable | Explicit path override |
| `--whisper-model` | Local GGML model file | Explicit path override |

The v1.0.0 local implementation writes files using an input-name, model and timestamp prefix. An output filename is **not** an Evidence ID and should not replace an evidence-management system's own identifiers.

## Output profiles

| Profile | Files kept |
| --- | --- |
| Normal | `*.integrado.json` |
| Quality | `*.integrado.json`, `*.qualidade.json` |
| Debug | Integrated, quality, raw whisper.cpp JSON, full diarization JSON, processing log |

When diarization is disabled, the Debug profile has no diarization JSON. Diagnostic logs and QA reports may contain private absolute input paths—redact before sharing.

## Minimal integrated output shape

```json
{
  "segments": [
    {
      "start": 1.2,
      "end": 2.8,
      "text": "An illustrative, fictional phrase.",
      "words": [
        {
          "word": "An",
          "start": 1.2,
          "end": 1.36,
          "score": 0.82,
          "speaker": "SPEAKER_00"
        }
      ],
      "speaker": "SPEAKER_00"
    }
  ],
  "language": "pt"
}
```

This is a **synthetic schema illustration**, not a real transcribed recording. In the actual output, words may lack a speaker or timestamps when the models could not assign them, and segments may contain words from multiple speakers. A `score` measures the alignment stage, not a calibrated probability of ASR correctness.

## What QA contributes

The quality report records stage status, backend detection, per-stage timing, operator evidence, counts and review flags (for example low alignment scores, long segments, unlabeled words and model-detected overlap). It does **not** correct transcripts automatically.

Raw ASR preserves the pre-alignment recognition output. Full diarization preserves regular and exclusive intervals and detected overlaps. The log records subprocess commands and backend evidence for debugging.

Use [the original recording](PROJECT_STORY.md) to resolve important ambiguity and [validation guidance](VALIDATION.md) to interpret flags.
