# Framework transcript JSON adapter — observed goals and release limits

**Status:** local adapter observed in November 2026. Not a published stable JSON Schema, SDK or distributed exporter.

The local operator interface is intended to deliver exactly **one `<filename>.framework.json` per media source**, keeping QA reports, temporary PCM, raw ASR, diarization evidence and resumable cache in separate private storage.

## Expected semantics

| Group | Meaning |
| --- | --- |
| Identity/provenance | Evidence ID, authorized recording reference and fingerprint, origin/tool/profile |
| Review | Derived transcript, `UNREVIEWED` until a human checks relevant passages |
| Content | Original recognized text in stable ordered segments with start/end times |
| Speakers | Anonymous labels, word-level disagreements or mixed turns flagged rather than falsely simplified |
| Quality | Backend and processing evidence, coverage metrics, unsupported words/short-window warnings |
| Retrieval | Optional bounded time buckets referencing segment IDs without duplicating or rewriting transcript text |

Illustration only (fictional, **not** a verified byte-for-byte export):

~~~json
{
  "schema": "nelx.framework-transcript.v1",
  "evidence": {
    "id": "EVD-EXAMPLE-001",
    "review_status": "UNREVIEWED"
  },
  "segments": [
    {
      "id": "SEG-0001",
      "start_ms": 0,
      "end_ms": 1480,
      "speaker_id": null,
      "text": "Fictional sentence for illustration.",
      "review_flags": ["MULTIPLE_AUTO_SPEAKERS"]
    }
  ]
}
~~~

The actual local file may use additional fields or different nesting. A sanitized exporter fixture, JSON Schema and tests are **required before** consumers hard-code an exact binding or this becomes a formal public API.

## Governance and privacy

A transcript is derived evidence, **not** an approved stakeholder requirement or verified decision. Preserve source provenance and reviewer corrections rather than silently rewriting raw ASR. Anonymous speaker labels do not identify people; time alignment coverage does not equal WER. Store actual recordings and client transcripts in approved private locations only.

This adapter is inspired by the consuming [operating framework's evidence-ingestion policy](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system/blob/main/docs/EVIDENCE_INGESTION.md), but the schema belongs to this Toolkit and its adopting private runtime; it is not declared to be an official operating-framework JSON standard.
