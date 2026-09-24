"""Local source-import regression checks; run after source-requirements.txt."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch


SPEC = importlib.util.spec_from_file_location("source_index", Path(__file__).with_name("index_teaching_sources.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

HEADER = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"


class SourceIndexTests(unittest.TestCase):
    def run_page(self, output: str) -> tuple[dict, dict, list[str]]:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "page.json"
            job = {"cache_path": str(path), "sha256": "example", "source_id": "source-01",
                   "page": 1, "language": "nld", "dpi": 110, "rotation": 0,
                   "tessdata": directory, "pdf": "private.pdf"}
            process = MagicMock(stdout=output.encode("utf-8"), stderr=b"")
            with patch.object(MODULE.fitz, "open") as pdf, patch.object(MODULE.subprocess, "run", return_value=process) as run:
                pdf.return_value.__enter__.return_value.__getitem__.return_value.get_pixmap.return_value.tobytes.return_value = b"PNG"
                public = MODULE.process_page(job)
            return public, json.loads(path.read_text()), run.call_args.args[0]

    def test_private_text_is_excluded_from_public_output(self):
        public, private, command = self.run_page(HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t20\t10\t91\timperfectum\n")
        self.assertEqual(private["text"], "imperfectum")
        self.assertNotIn("text", public)
        self.assertEqual(public["word_count"], 1)
        self.assertEqual(public["grammar_candidates"], ["past-tense"])
        self.assertIn("tessedit_create_tsv=1", command)

    def test_plain_text_instead_of_tsv_cannot_succeed(self):
        public, private, _ = self.run_page("PRIVATE handwritten answer\n")
        self.assertEqual(public["status"], "ocr_failed")
        self.assertEqual(private["error"], "ValueError")
        self.assertNotIn("PRIVATE", json.dumps(public))

    def test_empty_recognition_needs_review(self):
        public, _, _ = self.run_page(HEADER)
        self.assertEqual(public["status"], "ocr_empty_needs_review")

    def test_grammar_candidates_use_word_boundaries(self):
        self.assertEqual(MODULE.grammar_candidates("imperfectum"), ["past-tense"])
        self.assertIn("perfect-tense", MODULE.grammar_candidates("Het perfectum"))


if __name__ == "__main__":
    unittest.main()
