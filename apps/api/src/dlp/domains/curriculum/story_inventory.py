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
    """Compare written quantities without mistaking decimal punctuation for a fact change.

    Decimal commas, points, Arabic decimal marks and clock colons are deliberately
    treated alike in this conservative screen. Units and the distinction between a
    time and a price still need editorial review. Local date orders are excluded.
    """
    text = "".join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    text = text.replace("٫", ".").replace("٬", ",")
    text = re.sub(r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b", "", text)
    values = re.findall(r"(?<!\w)\d+(?:[.,:]\d+)*(?!\w)", text)
    return {value.replace(",", ".").replace(":", ".") for value in values}


def _legacy_audit(content: Path, *, minimum_stories: int = 200, minimum_words: int = 150) -> dict:
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



def _source_records(content: Path) -> tuple[list[dict], list[dict]]:
    """Read all representations; source identities, not filenames, define works."""
    from dlp.domains.study.reading_sources import read_reading_batches

    records: list[dict] = []
    issues: list[dict] = []
    originals: dict[str, str] = {}

    def add(stage: str, path: Path, item: dict, kind: str) -> None:
        identity = item.get("id", "")
        lines = item.get("lines")
        authored = isinstance(lines, list) and 8 <= len(lines) <= 12
        source = item.get("source_id") if kind == "guided" else None
        canonical = source or identity
        if source and originals.get(source) != stage:
            issues.append({"code": "invalid_canonical_source", "severity": "error", "story_id": identity,
                           "source_id": source, "stage": stage})
        units = lines if isinstance(lines, list) else item.get("paragraphs", [])
        text = " ".join(unit.get("nl", "") for unit in units
                        if isinstance(unit, dict) and isinstance(unit.get("nl"), str))
        records.append({"id": identity, "canonical_id": canonical, "stage_id": stage,
                        "source_kind": kind, "source_id": identity,
                        "lesson_id": identity if kind != "library" else None,
                        "path": str(path.relative_to(content)), "title": item.get("title", {}),
                        "lines": lines if isinstance(lines, list) else [], "text": text, "authored": authored,
                        "topic_id": item.get("topic_id"), "plot_key": item.get("plot_key", ""),
                        "vocabulary_ids": item.get("vocabulary_ids", [])})

    for stage in STAGES:
        for directory in PACKS:
            path = content / directory / f"{stage}.json"
            if not path.exists():
                continue
            for item in json.loads(path.read_text(encoding="utf-8")).get("stories", []):
                originals[item.get("id", "")] = stage
                add(stage, path, item, "library")
    for stage in STAGES:
        path = content / "study/packs" / f"{stage}.json"
        if not path.exists():
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("stage_id") != stage or document.get("schema_version") != 1:
            issues.append({"code": "pack_stage_mismatch", "severity": "error",
                           "story_id": str(path.relative_to(content))})
        for item in document.get("lessons", []):
            add(stage, path, item, "guided")
    for stage, path, document in read_reading_batches(content):
        location = str(path.relative_to(content))
        if (stage not in STAGES or document.get("stage_id") != stage or document.get("schema_version") != 1
                or document.get("language_variety") != "nl-BE" or document.get("review_status") != "unreviewed"):
            issues.append({"code": "invalid_reading_batch", "severity": "error", "story_id": location})
        for item in document.get("lessons", []):
            add(stage, path, item, "reading")
    return records, issues


def _line_findings(record: dict) -> list[dict]:
    """Local structural checks shared by every publishable reading representation."""
    issues = []
    identity = record["id"]

    def add(code: str, severity: str = "error", **details) -> None:
        issues.append({"code": code, "severity": severity, "story_id": identity, **details})

    lines = record["lines"]
    if not record["authored"]:
        if record["source_kind"] != "library":
            add("authored_line_count", count=len(lines))
        return issues
    if record["source_kind"] == "reading" and not record["plot_key"].strip():
        add("missing_story_plot_key")
    if record["source_kind"] != "library":
        if not isinstance(identity, str) or not identity.startswith(record["stage_id"] + "-"):
            add("invalid_story_identity")
        if any(not isinstance(record["title"].get(language), str) or not record["title"][language].strip()
               for language in ("nl", "en")):
            add("missing_story_title")
    for language in ("nl", "en"):
        values = [line.get(language, "") if isinstance(line, dict) else "" for line in lines]
        if any(not isinstance(value, str) or not value.strip() for value in values):
            add("missing_story_translation", language=language)
        complete = [value for value in values if isinstance(value, str) and value.strip()]
        normalized = [" ".join(tokens(value)) for value in complete]
        if len(normalized) != len(set(normalized)):
            add("repeated_story_line", language=language)
    for number, line in enumerate(lines, 1):
        if not isinstance(line, dict):
            continue
        if isinstance(line.get("nl"), str) and len(line["nl"]) > 600:
            add("line_exceeds_audio_limit", line=number)
        amounts = {language: quantities(line[language]) for language in ("nl", "en")
                   if isinstance(line.get(language), str)}
        # A missing numeric fact in one language is also a review candidate.
        if len(amounts) == 2 and any(amounts.values()) and amounts["nl"] != amounts["en"]:
            add("numeric_translation_review", "warning", line=number,
                quantities={language: sorted(value) for language, value in amounts.items()})
    return issues


def _similarity_findings(records: list[dict]) -> list[dict]:
    """Screen all sources together; legitimate representations of one work are aliases."""
    issues = []
    exact: dict[str, dict] = {}
    surface_variants: dict[str, dict] = {}
    titles: dict[str, dict] = {}
    postings: dict[tuple[str, ...], list[int]] = defaultdict(list)
    previous_shingles = []
    for index, record in enumerate(records):
        text = normal(record["text"])
        previous = exact.get(text)
        if text and previous and previous["canonical_id"] != record["canonical_id"]:
            issues.append({"code": "exact_story_duplicate", "severity": "error", "story_id": record["id"],
                           "other_id": previous["id"]})
        elif text:
            exact[text] = record
        # Changing only a name, a capitalised place or a number is still the
        # same teaching scene. This conservative flag requires identical other
        # words; it is not a claim to recognise semantically similar plots.
        surface = re.sub(r"\b[A-ZÀ-Ý][^\W_]*\b", "persoon", record["text"])
        surface = re.sub(r"\d+", "getal", surface)
        surface = " ".join(tokens(surface))
        previous = surface_variants.get(surface)
        if (len(tokens(text)) >= 12 and previous and previous["canonical_id"] != record["canonical_id"]
                and text != normal(previous["text"])):
            issues.append({"code": "surface_variant_needs_review", "severity": "warning", "story_id": record["id"],
                           "other_id": previous["id"]})
        elif surface:
            surface_variants[surface] = record
        title = normal(record["title"].get("nl", ""))
        previous = titles.get(title)
        if title and previous and previous["stage_id"] != record["stage_id"]:
            issues.append({"code": "cross_stage_repeated_title", "severity": "warning", "story_id": record["id"],
                           "other_id": previous["id"]})
        elif title:
            titles[title] = record
        pieces = shingles(text)
        if len(tokens(text)) >= 25:
            candidates = Counter(candidate for piece in pieces for candidate in postings[piece])
            for candidate, overlap in candidates.items():
                other = records[candidate]
                if record["canonical_id"] == other["canonical_id"] or text == normal(other["text"]):
                    continue
                smaller = min(len(pieces), len(previous_shingles[candidate]))
                if smaller >= 15 and overlap / smaller >= .85:
                    issues.append({"code": "near_copy_needs_review", "severity": "warning", "story_id": record["id"],
                                   "other_id": other["id"], "shingle_containment": round(overlap / smaller, 3)})
            for piece in pieces:
                postings[piece].append(index)
        previous_shingles.append(pieces)
    return issues


def audit(content: Path, *, minimum_stories: int = 200, minimum_words: int = 150) -> dict:
    """Count canonical 8–12-line drafts once, retaining findings about old short banks.

    ``authored_stories`` and ``eligible_authored_stories`` now include the guided
    course and reading batches. Explicit ``legacy_library_*`` fields preserve the
    older /library endpoint's narrower inventory. Structural eligibility never
    implies editorial, translation or CEFR approval.
    """
    legacy = _legacy_audit(content, minimum_stories=minimum_stories, minimum_words=minimum_words)
    records, source_issues = _source_records(content)
    issues = [*legacy["issues"], *source_issues]
    for record in records:
        issues.extend(_line_findings(record))
    issues.extend(_similarity_findings(records))
    # Preserve one finding when the old and unified screens identify the same issue.
    issues = list({json.dumps(item, sort_keys=True, ensure_ascii=False): item for item in issues}.values())

    grouped: dict[str, list[dict]] = defaultdict(list)
    identities: dict[str, dict] = {}
    for record in records:
        grouped[record["canonical_id"]].append(record)
        previous = identities.get(record["id"])
        if previous and previous["path"] != record["path"]:
            issues.append({"code": "duplicate_story_id", "severity": "error", "story_id": record["id"]})
        identities[record["id"]] = record

    provenance = content / "alignment/story-provenance.json"
    declared = json.loads(provenance.read_text(encoding="utf-8")).get("stories", []) if provenance.exists() else []
    plots = {item.get("story_id"): item.get("plot_key", "") for item in declared}
    selected = []
    rank = {"library": 0, "guided": 1, "reading": 2}
    for canonical, representations in grouped.items():
        candidates = [record for record in representations if record["authored"]]
        if not candidates:
            continue
        candidate = max(candidates, key=lambda item: rank[item["source_kind"]])
        if len({record["stage_id"] for record in representations}) != 1:
            issues.append({"code": "canonical_story_stage_mismatch", "severity": "error",
                           "story_id": candidate["id"]})
        if not candidate["plot_key"]:
            candidate["plot_key"] = plots.get(canonical, "")
        selected.append(candidate)
    seen_plots = {}
    for candidate in selected:
        key = normal(candidate["plot_key"])
        if key and key in seen_plots and seen_plots[key]["canonical_id"] != candidate["canonical_id"]:
            issues.append({"code": "repeated_plot_synopsis", "severity": "error", "story_id": candidate["id"],
                           "other_id": seen_plots[key]["id"]})
        elif key:
            seen_plots[key] = candidate
    invalid_ids = {item["story_id"] for item in issues if item["severity"] == "error"
                   or item["code"] in {"near_copy_needs_review", "surface_variant_needs_review"}}
    canonical_records = []
    for candidate in selected:
        canonical_records.append({
            "canonical_id": candidate["canonical_id"], "stage_id": candidate["stage_id"],
            "source_kind": candidate["source_kind"], "source_id": candidate["source_id"],
            "lesson_id": candidate["lesson_id"], "path": candidate["path"],
            "title": {language: candidate["title"].get(language, "") for language in ("nl", "en")},
            "lines": [{language: line.get(language, "") for language in ("nl", "en")}
                      for line in candidate["lines"] if isinstance(line, dict)],
            "topic_id": candidate["topic_id"], "plot_key": candidate["plot_key"],
            "aliases": sorted({record["id"] for record in grouped[candidate["canonical_id"]]}),
            "eligible": candidate["id"] not in invalid_ids and candidate["path"] not in invalid_ids,
        })
    rows = []
    for row in legacy["stages"]:
        candidates = [record for record in canonical_records if record["stage_id"] == row["stage"]]
        eligible = [record for record in candidates if record["eligible"]]
        library_ids = [identity for identity in row["eligible_authored_story_ids"] if identity not in invalid_ids]
        rows.append({**row,
                     "legacy_library_stories_total": row["stories_total"],
                     "legacy_library_authored_stories": row["authored_stories"],
                     "legacy_library_eligible_stories": len(library_ids),
                     "legacy_library_eligible_story_ids": library_ids,
                     "authored_stories": len(candidates), "eligible_authored_stories": len(eligible),
                     "eligible_authored_story_ids": [record["canonical_id"] for record in eligible],
                     "authored_story_shortfall": max(0, minimum_stories - len(eligible)),
                     "story_sources": dict(Counter(record["source_kind"] for record in eligible))})
    candidate_ids = {record["id"] for record in records if record["authored"] or record["source_kind"] != "library"}
    structural_errors = sum(item["severity"] == "error" for item in issues)
    canonical_errors = sum(item["severity"] == "error" and (item["story_id"] in candidate_ids
                           or item["story_id"].startswith("study/")) for item in issues)
    shortfall = any(row["authored_story_shortfall"] or row["vocabulary_shortfall"] for row in rows)
    return {**legacy, "schema_version": 2, "stages": rows, "issues": issues,
            "canonical_stories": canonical_records, "structural_errors": structural_errors,
            "canonical_structural_errors": canonical_errors,
            "inventory_status": "incomplete" if shortfall else "target_count_met_needs_editorial_review"}


def canonical_story_records(content: Path, stage_id: str | None = None) -> list[dict]:
    """Plain JSON reading references; callers publish only records with eligible=True."""
    return [record for record in audit(content)["canonical_stories"]
            if stage_id is None or record["stage_id"] == stage_id]
