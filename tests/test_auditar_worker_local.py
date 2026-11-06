"""Read-only auditor regressions, without opening real local worker files."""
from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import auditar_worker_local as audit


class AuditContractTest(unittest.TestCase):
    def test_same_source_has_matching_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker = Path(tmp) / "worker.py"
            worker.write_text('def run():\n    return "exclusive_intervals"\n', encoding="utf-8")
            report = audit.compare(audit.collect(worker), audit.collect(worker))
            self.assertEqual(report["status"], "MATCH_EXATO")
            self.assertEqual(report["funcoes_modificadas"], [])

    def test_missing_exclusive_and_changed_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / "installed.py"
            candidate = Path(tmp) / "candidate.py"
            installed.write_text('def run():\n    return {"intervals": []}\n', encoding="utf-8")
            candidate.write_text('def run():\n    return {"intervals": [], "exclusive_intervals": []}\n', encoding="utf-8")
            report = audit.compare(audit.collect(installed), audit.collect(candidate))
            self.assertEqual(report["status"], "DIVERGENCIA_ESTRUTURAL")
            self.assertIn("exclusive_intervals", report["local_sinais_ausentes"])
            self.assertIn("run", report["funcoes_modificadas"])
            self.assertFalse(report["worker_local_tem_intervalos_exclusivos"])

    def test_comment_only_difference_does_not_prove_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = Path(tmp) / "installed.py"
            candidate = Path(tmp) / "candidate.py"
            installed.write_text('def run():\n    return 1\n', encoding="utf-8")
            candidate.write_text('# comment\ndef run():\n    return 1\n', encoding="utf-8")
            report = audit.compare(audit.collect(installed), audit.collect(candidate))
            self.assertEqual(report["status"], "DIFERENCA_NAO_FUNCIONAL_OU_EXTERNA")
            self.assertNotEqual(report["worker_local_sha256"], report["worker_publicado_sha256"])

    def test_invalid_python_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "invalid.py"
            broken.write_text("def run(:", encoding="utf-8")
            with self.assertRaises(SyntaxError):
                audit.collect(broken)


if __name__ == "__main__":
    unittest.main()
