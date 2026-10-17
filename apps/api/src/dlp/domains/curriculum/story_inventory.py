"""Audit authored story structure and duplication without certifying language quality.

Default mode reports legacy material and unfinished targets without blocking a
release. Use --strict for structural errors, and --require-targets to require the
requested authored-story inventory. Neither mode establishes CEFR calibration,
plot coherence, natural Dutch or translation accuracy; these need editorial review.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from dlp.domains.curriculum.schemas import STAGE_IDS

STAGES = STAGE_IDS
LANGS = ("nl", "en", "fa")
PACKS = ("library", "source-lessons", "learning-units", "reading-library")


def normal(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def tokens(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", normal(text), flags=re.UNICODE)


def shingles(text: str, width: int = 5) -> set[tuple[str, ...]]:
    words = tokens(text)
    return {tuple(words[i:i + width]) for i in range(len(words) - width + 1)}


def quantities(text: str) -> set[str]:
    """Conservative digit screen; dates are excluded because local orders vary."""
    text = "".join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    text = re.sub(r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b", "", text)
    text = re.sub(r"\b(\d{1,2})[.:](\d{2})\b", r"\1:\2", text)
    return set(re.findall(r"(?<!\w)\d+(?:[.,:]\d+)*(?!\w)", text))


def audit(content: Path, *, minimum_stories: int = 200, minimum_words: int = 150) -> dict:
    issues: list[dict] = []
    records: list[dict] = []
    stage_rows = []
    core_contexts: dict[str, tuple[str, str]] = {}

    def issue(code: str, severity: str, story_id: str, **details) -> None:
        issues.append({"code": code, "severity": severity, "story_id": story_id, **details})

    for stage in STAGES:
        stories = []
        vocabulary = []
        for directory in PACKS:
            path = content / directory / f"{stage}.json"
            if not path.exists():
                continue
            pack = json.loads(path.read_text(encoding="utf-8"))
            if pack.get("stage_id") != stage:
                issue("pack_stage_mismatch", "error", str(path.relative_to(content)))
            stories.extend(pack.get("stories", []))
            vocabulary.extend(pack.get("vocabulary", []))
        ids = Counter(story.get("id", "") for story in stories)
        for story_id, count in ids.items():
            if count > 1:
                issue("duplicate_story_id", "error", story_id, count=count)
        authored = 0
        legacy = 0
        for story in stories:
            story_id = story.get("id", "")
            paragraphs = story.get("paragraphs", [])
            lines = story.get("lines")
            if lines is None:
                legacy += 1
            elif not isinstance(lines, list) or not 8 <= len(lines) <= 12:
                issue("authored_line_count", "error", story_id,
                      count=len(lines) if isinstance(lines, list) else None)
            else:
                authored += 1
            units = lines if isinstance(lines, list) else paragraphs
            texts = {}
            for lang in LANGS:
                values = [part.get(lang, "") if isinstance(part, dict) else "" for part in units]
                if any(not isinstance(value, str) or not value.strip() for value in values) or not values:
                    issue("missing_story_translation", "error", story_id, language=lang)
                    values = [value for value in values if isinstance(value, str)]
                texts[lang] = " ".join(values)
                if isinstance(lines, list):
                    paragraph_text = " ".join(part.get(lang, "") for part in paragraphs
                                              if isinstance(part, dict) and isinstance(part.get(lang), str))
                    if normal(paragraph_text) != normal(texts[lang]):
                        issue("line_paragraph_mismatch", "error", story_id, language=lang)
            if isinstance(lines, list):
                for index, line in enumerate(lines):
                    if not isinstance(line, dict):
                        continue
                    if isinstance(line.get("nl"), str) and len(line["nl"]) > 600:
                        issue("line_exceeds_audio_limit", "error", story_id, line=index + 1)
                    amounts = {lang: quantities(line[lang]) if isinstance(line.get(lang), str) else set() for lang in LANGS}
                    present = {lang: value for lang, value in amounts.items() if value}
                    if len(present) >= 2 and len({tuple(sorted(value)) for value in present.values()}) > 1:
                        issue("numeric_translation_review", "warning", story_id, line=index + 1,
                              quantities={lang: sorted(value) for lang, value in present.items()})
            records.append({"id": story_id, "stage": stage, "text": texts["nl"],
                            "title": story.get("title", {}).get("nl", ""),
                            "authored": isinstance(lines, list) and 8 <= len(lines) <= 12})
        distinct_terms = len({normal(word["term"]) for word in vocabulary if isinstance(word.get("term"), str)})
        usage_path = content / "vocabulary-transfer" / f"{stage}.json"
        usage = json.loads(usage_path.read_text(encoding="utf-8"))["entries"] if usage_path.exists() else []
        core = [entry for entry in usage if entry.get("productive_core")]
        word_ids = {word.get("id") for word in vocabulary}
        core_ids: set[str] = set()
        core_orders: set[int] = set()
        for entry in core:
            contexts = entry.get("contexts", [])
            valid_copy = all(all(isinstance(context.get(key, {}).get(lang), str)
                                and context[key][lang].strip() for lang in LANGS)
                             for context in contexts for key in ("sentence", "setting", "production_prompt"))
            order = entry.get("core_order")
            if (entry.get("word_id") not in word_ids or len(contexts) != 3 or not valid_copy
                    or type(order) is not int or not 1 <= order <= 150 or order in core_orders
                    or len({normal(context.get("sentence", {}).get("nl", "")) for context in contexts}) != 3):
                issue("invalid_productive_core_entry", "error", entry.get("word_id", stage))
                continue
            core_ids.add(entry["word_id"])
            core_orders.add(order)
            for context in contexts:
                text = normal(context["sentence"]["nl"])
                previous = core_contexts.get(text)
                if previous and previous[0] != stage:
                    issue("cross_stage_core_example_repeated", "warning", entry["word_id"], other_id=previous[1])
                else:
                    core_contexts[text] = (stage, entry["word_id"])
        authored_targets = {ref for story in stories if story.get("lines") for ref in story.get("vocabulary_ids", [])}
        stage_rows.append({"stage": stage, "stories_total": len(stories), "authored_stories": authored,
                           "legacy_stories": legacy, "distinct_vocabulary": distinct_terms,
                           "productive_core_words": len(core_ids),
                           "productive_core_classes": dict(Counter(entry.get("part_of_speech") for entry in core)),
                           "core_words_in_authored_stories": len(core_ids & authored_targets),
                           "authored_story_shortfall": max(0, minimum_stories - authored),
                           "vocabulary_shortfall": max(0, minimum_words - len(core_ids))})

    seen_texts: dict[str, dict] = {}
    seen_titles: dict[str, dict] = {}
    postings: dict[tuple[str, ...], list[int]] = defaultdict(list)
    story_shingles = []
    for index, record in enumerate(records):
        text = normal(record["text"])
        if text in seen_texts:
            issue("exact_story_duplicate", "error", record["id"], other_id=seen_texts[text]["id"])
        elif text:
            seen_texts[text] = record
        title = normal(record["title"])
        if title in seen_titles and seen_titles[title]["stage"] != record["stage"]:
            issue("cross_stage_repeated_title", "warning", record["id"], other_id=seen_titles[title]["id"])
        elif title:
            seen_titles[title] = record
        pieces = shingles(text)
        if len(tokens(text)) >= 25:
            candidates = Counter(candidate for piece in pieces for candidate in postings[piece])
            for candidate, overlap in candidates.items():
                other = records[candidate]
                if text == normal(other["text"]):
                    continue  # Exact copies have a stronger, separate finding.
                smaller = min(len(pieces), len(story_shingles[candidate]))
                if smaller >= 15 and overlap / smaller >= .85:
                    issue("near_copy_needs_review", "warning", record["id"], other_id=other["id"],
                          shingle_containment=round(overlap / smaller, 3))
            for piece in pieces:
                postings[piece].append(index)
        story_shingles.append(pieces)
    provenance_path = content / "alignment/story-provenance.json"
    if provenance_path.exists():
        seen_plots = {}
        declared = json.loads(provenance_path.read_text(encoding="utf-8")).get("stories", [])
        story_ids = {record["id"] for record in records}
        for item in declared:
            key = normal(item.get("plot_key", ""))
            if not key or item.get("story_id") not in story_ids:
                issue("invalid_story_provenance", "error", item.get("story_id", ""))
            elif key in seen_plots:
                issue("repeated_plot_synopsis", "error", item["story_id"], other_id=seen_plots[key])
            else:
                seen_plots[key] = item["story_id"]
    invalid_ids = {item["story_id"] for item in issues if item["severity"] == "error"
                   or item["code"] == "near_copy_needs_review"}
    for row in stage_rows:
        row["eligible_authored_story_ids"] = [record["id"] for record in records
                                               if record["stage"] == row["stage"] and record["authored"]
                                               and record["id"] not in invalid_ids]
        row["eligible_authored_stories"] = len(row["eligible_authored_story_ids"])
        row["authored_story_shortfall"] = max(0, minimum_stories - row["eligible_authored_stories"])
    errors = sum(issue["severity"] == "error" for issue in issues)
    shortfall = any(row["authored_story_shortfall"] or row["vocabulary_shortfall"] for row in stage_rows)
    return {"schema_version": 1,
            "claim": "Structural audit only; coherence, CEFR suitability and translation accuracy need editorial review.",
            "targets": {"authored_stories_per_stage": minimum_stories, "vocabulary_per_stage": minimum_words},
            "inventory_status": "incomplete" if shortfall else "target_count_met_needs_editorial_review",
            "structural_errors": errors, "stages": stage_rows, "issues": issues}

