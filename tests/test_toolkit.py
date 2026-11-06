"""Synthetic regression: no model downloads, private audio or GPU."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from n3lx_toolkit import export_framework as export
from n3lx_toolkit import monitor
from n3lx_toolkit import qa_unificado


class ExporterTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name)
        self.media = folder / "2026-11-05 00-00-00.mkv"
        self.media.write_bytes(b"synthetic bytes, not a real recording")
        self.integrated = folder / "integrado.json"
        self.qa = folder / "qa_report.json"
        self.quality = folder / "integracao-qualidade.json"
        self.integrated.write_text(json.dumps({
            "language": "pt", "metadata": {"backend_asr": "vulkan"},
            "segments": [
                {"start": 0.0, "end": 0.8, "text": "Bom dia", "words": [
                    {"word": "Bom", "start": 0.1, "end": 0.3, "speaker": "SPEAKER_00"},
                    {"word": "dia", "start": 0.4, "end": 0.6, "speaker": "SPEAKER_01"}]},
                {"start": 0.8, "end": 1.2, "text": "Teste", "words": [
                    {"word": "Teste", "start": 0.9, "end": 1.1, "speaker": "SPEAKER_01"}]}
            ]}), encoding="utf-8")
        self.quality.write_text(json.dumps({
            "status": "PASS", "segments": 2, "words_total": 3, "words_aligned": 3,
            "words_with_speaker": 3, "word_coverage": 1.0, "speaker_coverage": 1.0,
            "warnings": []}), encoding="utf-8")
        self.report = {
            "qa_version": "2026-11-06.2-bs5", "source": str(self.media),
            "source_bytes": self.media.stat().st_size,
            "stages": {key: {"status": "PASS", "details": {}}
                       for key in export.STAGES}}
        self.report["stages"]["audio_16khz"]["details"]["duration_seconds"] = 1.2
        self.save_report()

    def save_report(self):
        self.qa.write_text(json.dumps(self.report), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self):
        return export.make_export(self.media, self.integrated, self.qa, self.quality)

    def test_preserves_text_and_mixed_speakers(self):
        result = self.payload()
        self.assertEqual([s["text"] for s in result["segments"]], ["Bom dia", "Teste"])
        self.assertIsNone(result["segments"][0]["speaker_id"])
        self.assertEqual(result["segments"][0]["speaker_candidates"],
                         ["SPEAKER_00", "SPEAKER_01"])
        self.assertEqual(result["evidence"]["review_status"], "UNREVIEWED")
        self.assertEqual(result["transcription"]["asr_beam_size"], 5)
        self.assertNotIn(str(self.media.parent), json.dumps(result))

    def test_repeated_export_and_conflict(self):
        output = self.media.parent / "transcricao" / "sample.framework.json"
        result = self.payload()
        self.assertEqual(export.write_new_or_identical(output, result), "CREATED")
        self.assertEqual(export.write_new_or_identical(output, result), "REUSED_IDENTICAL")
        with self.assertRaises(FileExistsError):
            export.write_new_or_identical(output, {"different": True})
        self.assertEqual(json.loads(output.read_text()), result)

    def test_failing_qa_blocks_export(self):
        self.report["stages"]["integracao_final"]["status"] = "FAIL"
        self.save_report()
        with self.assertRaises(ValueError):
            self.payload()

    def test_source_mismatch_blocks_export(self):
        self.report["source_bytes"] += 10
        self.save_report()
        with self.assertRaises(ValueError):
            self.payload()


class MonitorTest(unittest.TestCase):
    def test_asr_timestamp(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "asr.log"
            self.assertIsNone(monitor.last_asr_seconds(path))
            path.write_bytes(b"[00:00:05.000 --> 00:00:08.500]\n")
            self.assertAlmostEqual(monitor.last_asr_seconds(path), 8.5)

    def test_no_invented_progress(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / "qa_report.json").write_text(json.dumps({
                "stages": {"preflight": {"status": "PASS", "details": {}},
                           "audio_16khz": {"status": "PASS",
                                          "details": {"duration_seconds": 120}}}}))
            log = base / "runner.log"
            log.write_text("Evidencias: " + str(base) + "\n== asr_vulkan ==\n")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                monitor.draw("fiction.mkv", log, 10)
            self.assertIn("EM EXECUCAO", stdout.getvalue())
            self.assertIn("sem timestamp parcial", stdout.getvalue())
            self.assertNotIn("50.0%", stdout.getvalue())


class ConfigurationTest(unittest.TestCase):
    def test_beam_size_separated_from_prior_cache(self):
        self.assertEqual(qa_unificado.VERSION, "2026-11-06.2-bs5")
        self.assertIn("bs5", qa_unificado.CACHE_VERSION)
        source = (ROOT / "src/n3lx_toolkit/qa_unificado.py").read_text(encoding="utf-8")
        self.assertNotIn("D:\\OBS Videos", source)
        self.assertIn('"-bs", "5"', source)


if __name__ == "__main__":
    unittest.main()
