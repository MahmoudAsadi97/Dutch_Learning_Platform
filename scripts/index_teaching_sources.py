#!/usr/bin/env python3
"""Index private scanned teaching PDFs without publishing their text.

Requires PyMuPDF and Tesseract with Dutch (nld) language data. The resumable
page records contain unverified OCR and must stay under .local or outside git.
Only metadata and rule-based grammar candidates enter the public index.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import re
import subprocess

import fitz


ROOT = Path(__file__).resolve().parents[1]
GRAMMAR_PATTERNS = {
    "present-tense": r"presens|tegenwoordige tijd",
    "past-tense": r"imperfectum|verleden tijd",
    "perfect-tense": r"perfectum|voltooid deelwoord|participium",
    "word-order": r"woordvolgorde|inversie|hoofdzin|bijzin",
    "separable-verbs": r"scheidbare werkwoorden|scheidbaar werkwoord",
    "modal-verbs": r"modale werkwoorden|modaal werkwoord",
    "negation": r"negatie|ontkenning",
    "articles": r"lidwoorden|lidwoord",
    "plural-nouns": r"meervoud|enkelvoud",
    "adjectives": r"adjectieven|adjectief|bijvoeglijk",
    "comparison": r"comparatief|superlatief|vergelijking|trappen van",
    "pronouns": r"pronomen|pronomina|voornaamwoord",
    "prepositions": r"prepositie|voorzetsel",
    "conjunctions": r"conjunctie|voegwoord",
    "relative-clauses": r"relatieve zin|relatieve zinnen|betrekkelijk",
    "passive": r"passief|passieve|lijdende vorm",
    "diminutives": r"diminutief|verkleinwoord",
    "imperative": r"imperatief|gebiedende wijs",
    "infinitive": r"infinitief|infinitieven",
    "spelling": r"spelling|klinker|medeklinker|alfabet",
    "numbers-time": r"telwoord|rangtelwoord|kloktijd",
    "reflexive-verbs": r"reflexief|reflexieve|wederkerend",
    "preferences-polite-requests": r"zou|zouden|graag|liever",
    "progressive": r"aan het",
    "existential-er": r"voorlopig subject|presentatief",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def page_recovery_settings(value: object, sources: dict[str, int]) -> dict:
    """Validate explicit page-level render adjustments before any OCR job starts."""
    if not isinstance(value, dict):
        raise ValueError("Recovery settings must be an object keyed by source ID")
    for source_id, mapping in value.items():
        if source_id not in sources or not isinstance(mapping, dict):
            raise ValueError("Recovery settings refer to an unknown source or invalid page mapping")
        for page, settings in mapping.items():
            if not isinstance(page, str) or not page.isdigit() or str(int(page)) != page or not 1 <= int(page) <= sources[source_id]:
                raise ValueError("Recovery settings refer to a nonexistent PDF page")
            if not isinstance(settings, dict) or set(settings) - {"dpi", "channel"}:
                raise ValueError("Page recovery permits only dpi and channel settings")
            if "dpi" in settings and (type(settings["dpi"]) is not int or not 72 <= settings["dpi"] <= 600):
                raise ValueError("Page recovery dpi must be an integer between 72 and 600")
            if "channel" in settings and settings["channel"] not in ("gray", "blue"):
                raise ValueError("Page recovery channel must be gray or blue")
    return value


def render_page(page, dpi: int, rotation: int, channel: str = "gray") -> bytes:
    """The blue plane separates dark text from pale blue worksheet backgrounds."""
    if channel not in ("gray", "blue"):
        raise ValueError("Unsupported page rendering channel")
    image = page.get_pixmap(
        matrix=fitz.Matrix(dpi / 72, dpi / 72).prerotate(rotation),
        colorspace=fitz.csRGB if channel == "blue" else fitz.csGRAY,
        alpha=False,
    )
    if channel == "blue":
        image = fitz.Pixmap(fitz.csGRAY, image.width, image.height, image.samples[2::3], False)
    return image.tobytes("png")


def process_page(job: dict) -> dict:
    destination = Path(job["cache_path"])
    channel = job.get("colour_channel", "gray")
    if destination.exists():
        cached = json.loads(destination.read_text())
        if cached.get("extractor_version") == 2 and cached.get("source_sha256") == job["sha256"] and cached.get("language") == job["language"] and cached.get("dpi") == job["dpi"] and cached.get("colour_channel", "gray") == channel and cached.get("rotation_degrees", 0) == job["rotation"] and cached.get("status") == "ocr_unverified" and cached.get("word_count", 0) > 0 and cached.get("text", "").strip():
            cached["grammar_candidates"] = grammar_candidates(cached["text"])
            cached.setdefault("colour_channel", "gray")
            cached.setdefault("ocr_psm", 3)
            cached.setdefault("ocr_attempted_psms", [3])
            write_json(destination, cached)
            return public_page(cached)
    row = {
        "source_id": job["source_id"], "pdf_page": job["page"],
        "extractor_version": 2,
        "source_sha256": job["sha256"], "language": job["language"],
        "dpi": job["dpi"], "colour_channel": channel, "rotation_degrees": job["rotation"],
        "status": "ocr_failed", "text": "",
        "word_count": 0, "mean_word_confidence": None,
        "grammar_candidates": [], "error": None,
        "ocr_psm": None, "ocr_attempted_psms": [],
    }
    try:
        with fitz.open(job["pdf"]) as document:
            image = render_page(document[job["page"] - 1], job["dpi"], job["rotation"], channel)
        for psm in (3, 11):
            # Automatic page segmentation misses some coloured worksheets.
            # Try sparse-text layout only after a valid TSV contains no words.
            # A nonempty result is kept, without another paid or remote service.
            row["ocr_attempted_psms"].append(psm)
            command = ["tesseract", "stdin", "stdout", "-l", job["language"], "--psm", str(psm)]
            if job["tessdata"]:
                command += ["--tessdata-dir", job["tessdata"]]
            # Custom tessdata may contain language data without the `tsv` config.
            command += ["-c", "tessedit_create_tsv=1"]
            result = subprocess.run(command, input=image, capture_output=True, timeout=90,
                                    env={**os.environ, "OMP_THREAD_LIMIT": "1"}, check=True)
            words, confidences, text = parse_ocr_tsv(result.stdout.decode("utf-8"))
            row["ocr_psm"] = psm
            if words:
                break
        row.update(status="ocr_unverified" if words else "ocr_empty_needs_review", text=text, word_count=len(words),
                   mean_word_confidence=round(sum(confidences) / len(confidences), 2) if confidences else None,
                   grammar_candidates=grammar_candidates(text))
    except (subprocess.SubprocessError, OSError, ValueError, KeyError) as exc:
        row["error"] = type(exc).__name__
    write_json(destination, row)
    return public_page(row)


def parse_ocr_tsv(output: str) -> tuple[list[str], list[float], str]:
    if not output.startswith("level\tpage_num\t"):
        raise ValueError("Tesseract did not return TSV")
    words, confidences, lines = [], [], {}
    for item in csv.DictReader(io.StringIO(output), delimiter="\t", quoting=csv.QUOTE_NONE):
        word = item.get("text", "").strip()
        if not word:
            continue
        words.append(word)
        confidence = float(item["conf"])
        if confidence >= 0:
            confidences.append(confidence)
        key = (item["block_num"], item["par_num"], item["line_num"])
        lines.setdefault(key, []).append(word)
    return words, confidences, "\n".join(" ".join(line) for line in lines.values())


def grammar_candidates(text: str) -> list[str]:
    return [name for name, pattern in GRAMMAR_PATTERNS.items()
            if re.search(r"\b(?:" + pattern + r")\b", text, re.I)]


def source_identifier(filename: str, digest: str) -> str:
    """Keep a download's copy suffix from changing the numbered source identity."""
    number = re.search(r"(\d+)(?:\(\d+\))?\.pdf$", filename, re.I)
    return f"source-{int(number.group(1)):02d}" if number else digest[:12]


def public_page(row: dict) -> dict:
    # Deliberate allowlist: never serialize text, token lists, images or errors.
    return {key: row[key] for key in (
        "source_id", "pdf_page", "status", "word_count",
        "mean_word_confidence", "grammar_candidates",
    )}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/source-import")
    parser.add_argument("--public-index", type=Path)
    parser.add_argument("--language", default="nld")
    parser.add_argument("--tessdata-dir", default="")
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rotations-file", type=Path, help="JSON {source-id: {PDF-page: clockwise-degrees}}")
    parser.add_argument("--recovery-file", type=Path, help="JSON {source-id: {PDF-page: {dpi: 220, channel: blue}}}")
    parser.add_argument("--only", nargs="*", help="Optional filenames to process; otherwise all PDFs")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / ".local"):
        parser.error("Private OCR inside this repository must be stored under .local/")
    if args.dpi < 72 or not 1 <= args.workers <= 16:
        parser.error("Use dpi >= 72 and between 1 and 16 workers")
    rotations = json.loads(args.rotations_file.read_text()) if args.rotations_file else {}
    if any(int(degrees) not in (0, 90, 180, 270) for mapping in rotations.values() for degrees in mapping.values()):
        parser.error("Page rotation must be 0, 90, 180 or 270 degrees")
    sources, jobs, pages = [], [], []
    seen_sources = {}
    for pdf in sorted(args.pdf_dir.glob("*.pdf")):
        if args.only and pdf.name not in args.only:
            continue
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        source_id = source_identifier(pdf.name, digest)
        if source_id in seen_sources:
            if seen_sources[source_id] != digest:
                parser.error(f"Different PDFs share {source_id}; use distinct source numbers")
            continue
        seen_sources[source_id] = digest
        with fitz.open(pdf) as document:
            count = len(document)
            native = sum(bool(page.get_text().strip()) for page in document)
        sources.append({"source_id": source_id, "filename": pdf.name, "sha256": digest,
                        "pdf_pages": count, "pages_with_embedded_text": native,
                        "rights_status": "owner_supplied_permission_not_established",
                        "audio_supplied": False})
        for page in range(1, count + 1):
            jobs.append({"pdf": str(pdf.resolve()), "source_id": source_id,
                         "page": page, "sha256": digest, "language": args.language,
                         "dpi": args.dpi, "tessdata": args.tessdata_dir,
                         "rotation": int(rotations.get(source_id, {}).get(str(page), 0)),
                         "cache_path": str(output / source_id / f"{page:04d}.json")})
    if not jobs:
        parser.error("No source PDFs found")
    try:
        recovery = page_recovery_settings(
            json.loads(args.recovery_file.read_text()) if args.recovery_file else {},
            {source["source_id"]: source["pdf_pages"] for source in sources},
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    for job in jobs:
        settings = recovery.get(job["source_id"], {}).get(str(job["page"]), {})
        job["dpi"] = settings.get("dpi", args.dpi)
        job["colour_channel"] = settings.get("channel", "gray")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(process_page, job) for job in jobs]
        for future in as_completed(futures):
            pages.append(future.result())
            if len(pages) % 25 == 0 or len(pages) == len(jobs):
                print(f"Indexed {len(pages)}/{len(jobs)} pages", flush=True)
    pages.sort(key=lambda row: (row["source_id"], row["pdf_page"]))
    manifest = {"schema_version": 1, "ocr_engine": "tesseract", "ocr_language": args.language,
                "dpi": args.dpi, "sources": sources, "total_pages": len(jobs),
                "ocr_completed": sum(page["status"] == "ocr_unverified" for page in pages),
                "ocr_failed": sum(page["status"] == "ocr_failed" for page in pages),
                "ocr_empty_needs_review": sum(page["status"] == "ocr_empty_needs_review" for page in pages),
                "review_status": "unverified_machine_extraction",
                "warning": "OCR confidence is not language accuracy. Grammar matches are navigation candidates, not teaching facts."}
    if recovery:
        manifest["page_recovery_settings"] = recovery
    write_json(output / "manifest.json", manifest)
    write_json(output / "pages.json", pages)
    tokens: dict[str, dict] = {}
    for job in jobs:
        record = json.loads(Path(job["cache_path"]).read_text())
        for token in set(re.findall(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", record["text"].lower())):
            if len(token) < 2:
                continue
            entry = tokens.setdefault(token, {
                "token": token, "pages": [], "review_status": "unverified_ocr_token",
                "candidate_kind": "surface_form_not_validated_lemma",
                "eligible_for_lessons": False,
                "confidence_measure": "page_mean_ocr_confidence_not_token_accuracy",
            })
            entry["pages"].append({"source_id": record["source_id"], "pdf_page": record["pdf_page"],
                                   "page_mean_confidence": record["mean_word_confidence"]})
    for entry in tokens.values():
        confidences = [page["page_mean_confidence"] for page in entry["pages"] if page["page_mean_confidence"] is not None]
        entry["page_count"] = len(entry["pages"])
        entry["mean_page_confidence"] = round(sum(confidences) / len(confidences), 2) if confidences else None
    write_json(output / "vocabulary-candidates.json", sorted(tokens.values(), key=lambda item: item["token"]))
    manifest["private_unique_token_candidates"] = len(tokens)
    write_json(output / "manifest.json", manifest)
    if args.public_index:
        write_json(args.public_index / "manifest.json", manifest)
        write_json(args.public_index / "pages.json", pages)
    print(f"Complete: {manifest['ocr_completed']} extracted, {manifest['ocr_failed']} failed. No OCR text printed.")
    return int(bool(manifest["ocr_failed"]))


if __name__ == "__main__":
    raise SystemExit(main())
