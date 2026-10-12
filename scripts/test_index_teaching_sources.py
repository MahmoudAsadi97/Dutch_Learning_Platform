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
    def test_download_copy_suffix_keeps_source_identity(self):
        for filename in ("Dutch pdf 9.pdf", "Dutch pdf 9(1).pdf", "Dutch pdf9(12).PDF"):
            self.assertEqual(MODULE.source_identifier(filename, "example"), "source-09")
        self.assertEqual(MODULE.source_identifier("notes.pdf", "abcdef1234567890"), "abcdef123456")

    def run_page(self, output: str | list[str]) -> tuple[dict, dict, list[list[str]]]:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "page.json"
            job = {"cache_path": str(path), "sha256": "example", "source_id": "source-01",
                   "page": 1, "language": "nld", "dpi": 110, "rotation": 0,
                   "tessdata": directory, "pdf": "private.pdf"}
            outputs = [output, output] if isinstance(output, str) else output
            processes = [MagicMock(stdout=value.encode("utf-8"), stderr=b"") for value in outputs]
            with patch.object(MODULE.fitz, "open") as pdf, patch.object(MODULE.subprocess, "run", side_effect=processes) as run:
                pdf.return_value.__enter__.return_value.__getitem__.return_value.get_pixmap.return_value.tobytes.return_value = b"PNG"
                public = MODULE.process_page(job)
            return public, json.loads(path.read_text()), [call.args[0] for call in run.call_args_list]

    def test_private_text_is_excluded_from_public_output(self):
        public, private, commands = self.run_page(HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t20\t10\t91\timperfectum\n")
        self.assertEqual(private["text"], "imperfectum")
        self.assertNotIn("text", public)
        self.assertEqual(public["word_count"], 1)
        self.assertEqual(public["grammar_candidates"], ["past-tense"])
        self.assertIn("tessedit_create_tsv=1", commands[0])
        self.assertEqual(len(commands), 1)
        self.assertEqual(private["ocr_attempted_psms"], [3])
        self.assertEqual(private["ocr_psm"], 3)
        self.assertNotIn("ocr_psm", public)

    def test_plain_text_instead_of_tsv_cannot_succeed(self):
        public, private, commands = self.run_page("PRIVATE handwritten answer\n")
        self.assertEqual(public["status"], "ocr_failed")
        self.assertEqual(private["error"], "ValueError")
        self.assertNotIn("PRIVATE", json.dumps(public))
        self.assertEqual(len(commands), 1)

    def test_empty_recognition_needs_review(self):
        public, private, commands = self.run_page(HEADER)
        self.assertEqual(public["status"], "ocr_empty_needs_review")
        self.assertEqual(private["ocr_attempted_psms"], [3, 11])
        self.assertEqual(private["ocr_psm"], 11)
        self.assertEqual(len(commands), 2)

    def test_sparse_layout_recovers_only_an_empty_page(self):
        sparse = HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t20\t10\t90\tGeen\n" + "5\t1\t1\t1\t1\t2\t25\t0\t20\t10\t84\tkoffie\n"
        public, private, commands = self.run_page([HEADER, sparse])
        self.assertEqual(public["status"], "ocr_unverified")
        self.assertEqual(public["word_count"], 2)
        self.assertEqual(public["mean_word_confidence"], 87)
        self.assertEqual(private["text"], "Geen koffie")
        self.assertEqual(private["ocr_psm"], 11)
        self.assertEqual([command[command.index("--psm") + 1] for command in commands], ["3", "11"])
        self.assertNotIn("Geen koffie", json.dumps(public))
        self.assertNotIn("ocr_attempted_psms", public)

    def test_nonempty_cache_is_reused_without_ocr(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "page.json"
            cached = {"extractor_version": 2, "source_sha256": "example", "language": "nld",
                      "dpi": 150, "rotation_degrees": 0, "status": "ocr_unverified",
                      "source_id": "source-01", "pdf_page": 30, "text": "imperfectum",
                      "word_count": 1, "mean_word_confidence": 81, "grammar_candidates": [],
                      "ocr_psm": 11, "ocr_attempted_psms": [3, 11]}
            path.write_text(json.dumps(cached))
            job = {"cache_path": str(path), "sha256": "example", "language": "nld",
                   "dpi": 150, "rotation": 0}
            with patch.object(MODULE.fitz, "open") as pdf, patch.object(MODULE.subprocess, "run") as run:
                public = MODULE.process_page(job)
            pdf.assert_not_called()
            run.assert_not_called()
            self.assertEqual(public["grammar_candidates"], ["past-tense"])
            self.assertEqual(json.loads(path.read_text())["ocr_psm"], 11)
            self.assertEqual(json.loads(path.read_text())["colour_channel"], "gray")

    def test_page_recovery_validates_sources_pages_and_only_render_settings(self):
        settings = {"source-01": {"30": {"dpi": 220, "channel": "blue"}}}
        self.assertEqual(MODULE.page_recovery_settings(settings, {"source-01": 120}), settings)
        invalid = [[], {"source-02": {}}, {"source-01": []},
                   {"source-01": {"0": {}}}, {"source-01": {"121": {}}},
                   {"source-01": {"030": {}}}, {"source-01": {"30": []}},
                   {"source-01": {"30": {"text": "must stay private"}}},
                   *({"source-01": {"30": {"dpi": dpi}}} for dpi in (71, 601, True, "220")),
                   {"source-01": {"30": {"channel": "red"}}}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                MODULE.page_recovery_settings(value, {"source-01": 120})

    def test_blue_renderer_uses_exact_blue_plane_without_alpha(self):
        page = MagicMock()
        rgb = page.get_pixmap.return_value
        rgb.width, rgb.height = 2, 1
        rgb.samples = bytes((10, 20, 30, 40, 50, 60))
        image = MODULE.fitz.Pixmap(MODULE.render_page(page, 220, 90, "blue"))
        self.assertEqual(image.samples, bytes((30, 60)))
        self.assertEqual(image.n, 1)
        self.assertEqual(image.alpha, 0)
        self.assertEqual(page.get_pixmap.call_args.kwargs["colorspace"], MODULE.fitz.csRGB)
        self.assertFalse(page.get_pixmap.call_args.kwargs["alpha"])

    def test_cache_identity_distinguishes_render_channel_and_effective_dpi(self):
        for dpi, channel in ((150, "blue"), (220, "gray")):
            with self.subTest(dpi=dpi, channel=channel), TemporaryDirectory() as directory:
                path = Path(directory) / "page.json"
                cached = {"extractor_version": 2, "source_sha256": "example", "language": "nld",
                          "dpi": 150, "rotation_degrees": 0, "status": "ocr_unverified",
                          "source_id": "source-01", "pdf_page": 30, "text": "old gray OCR",
                          "word_count": 3, "mean_word_confidence": 81, "grammar_candidates": []}
                path.write_text(json.dumps(cached))
                job = {"cache_path": str(path), "sha256": "example", "source_id": "source-01",
                       "page": 30, "language": "nld", "dpi": dpi, "rotation": 0,
                       "colour_channel": channel, "tessdata": "", "pdf": "private.pdf"}
                result = MagicMock(stdout=(HEADER + "5\t1\t1\t1\t1\t1\t0\t0\t20\t10\t91\tRecovered\n").encode())
                with patch.object(MODULE.fitz, "open"), patch.object(MODULE, "render_page", return_value=b"PNG") as render, patch.object(MODULE.subprocess, "run", return_value=result) as run:
                    public = MODULE.process_page(job)
                    self.assertEqual(run.call_count, 1)
                    self.assertEqual(render.call_args.args[1:], (dpi, 0, channel))
                private = json.loads(path.read_text())
                self.assertEqual(private["text"], "Recovered")
                self.assertEqual(private["dpi"], dpi)
                self.assertEqual(private["colour_channel"], channel)
                self.assertNotIn("colour_channel", public)
                with patch.object(MODULE.fitz, "open") as pdf, patch.object(MODULE.subprocess, "run") as run:
                    MODULE.process_page(job)
                pdf.assert_not_called()
                run.assert_not_called()

    def test_grammar_candidates_use_word_boundaries(self):
        self.assertEqual(MODULE.grammar_candidates("imperfectum"), ["past-tense"])
        self.assertIn("perfect-tense", MODULE.grammar_candidates("Het perfectum"))


if __name__ == "__main__":
    unittest.main()
