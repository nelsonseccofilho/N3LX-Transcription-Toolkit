# Community-1 / DirectML worker — recovered candidate contract

**Status:** reconstructed from an archived first-party worker, synthetically tested, but **not** proven equivalent to the final worker installed on the Windows reference machine.

## Reason for recovery

The archived `diarizacao_directml_worker_corrigido(1).py` had provider checks, profiling and regular speaker turns but **did not emit `exclusive_intervals`**. The unified QA checks for both interval collections, and the CTC integration assigns automatic speakers using exclusive turns. Publishing the archived version unchanged would fail the current QA.

The updated developer candidate is at `src/n3lx_toolkit/diarizacao_directml_worker.py`. It loads the externally provided ONNX Community-1 implementation and reads both `result.speaker_diarization` and `result.exclusive_speaker_diarization`. It normalizes timestamps, rejects overlapping exclusive intervals and reports executed DirectML segmentation/embedding operators separately from ONNX CPU operators.

## Payload and contract

Illustrative **synthetic** payload (values are not hardware measurements or real speakers):

~~~json
{
  "backend": "onnx_directml_confirmado",
  "intervals": [{"start": 0.1, "end": 0.4, "speaker": "SPEAKER_00"}],
  "exclusive_intervals": [{"start": 0.1, "end": 0.4, "speaker": "SPEAKER_00"}],
  "operadores_directml": {"segmentacao": 1, "embedding": 1},
  "operadores_cpu_onnx": {"segmentacao": 0, "embedding": 0}
}
~~~

Input is mono 16 kHz 16-bit PCM WAV. Both interval sets must be present and nonempty for the current QA to pass. A missing model file, missing DirectML provider, missing DML operator evidence, invalid timestamp, or overlap in the exclusive stream prevents a successful result.

## External inputs and Windows environment

- `N3LX_WORKSPACE`: native Windows workspace for tools/models/venvs/QA.
- `N3LX_ONNX_PYANNOTE_REPO`: external checkout containing `onnx_pyannote.py` and its dependency utilities; rights and versions must be reviewed.
- `N3LX_DIARIZATION_MODELS`: external ONNX Community-1 model assets including segmentation, embedding, config and PLDA.
- `N3LX_DIARIZATION_WORKER`: optional path to the **original validated local worker** instead of the published candidate.

Model weights and the third-party ONNX pipeline are **not copied into the public repository**. The QA cache signature includes relevant ONNX, PLDA and worker files to prevent inappropriate reuse after code/model changes.

## Validation performed vs pending

**Performed:** recovered first-party source, checked the QA expected schema, compiled the candidate, and exercised synthetic regular/exclusive interval extraction and a mocked DirectML output path. The test suite also asserts the QA validator accepts this shape.

**Pending:** byte-for-byte comparison with the exact final Windows worker; standalone GPU `--check`; an authorized WAV on the actual AMD/DirectML runtime; parity of speaker turns against the installed reference; clean-machine setup and legal/third-party dependency review. Earlier GitHub Actions runs were blocked before a runner was assigned; hosted CI status must be checked independently. Synthetic testing is **not** hardware proof.

No installation scripts should replace the known-good local worker automatically.

## Next-cycle equalization evidence (read-only)

The source archive contains an **older** worker lacking `exclusive_intervals`; the exact final installed file is not available in the recovered archive. To avoid silently declaring parity, the Toolkit now includes `scripts/auditar_worker_local.py`, with synthetic tests for identical files, missing exclusive data, non-semantic differences and invalid Python. The auditor emits sanitized SHA-256 hashes and changed top-level function names, **not** private source lines or filesystem paths. Source checks are only an evidence collection step, not a GPU integration test. [Run instructions (PT-BR)](../pt-BR/AUDITORIA_WORKER_LOCAL.md).
