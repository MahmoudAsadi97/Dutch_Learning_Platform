"""Compile original story manuscripts and productive vocabulary into strict app packs.

Manuscripts are data, not executable templates. No language is inferred, translated,
conjugated or copied from news by this compiler. Inventory and editorial approval
are separate: counting a story never confers a language-review status.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from dlp.domains.curriculum.library import (
    LibraryStory,
    LibraryWord,
    StageLibrary,
    normalise,
)
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.curriculum.word_usage import ALL_STRUCTURES, STAGE_STRUCTURES

ROOT = Path(__file__).resolve().parents[2]


def prompts():
    path = Path(__file__).with_name("vocabulary_transfer.py")
    spec = importlib.util.spec_from_file_location("expansion_transfer_prompts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PROMPTS


PROMPTS = prompts()
CATEGORY = {"nl": "Verhaal naar gesprek", "en": "Story into conversation", "fa": "از داستان تا گفت‌وگو"}
GENRES = {
    "romance": {"nl": "Liefde", "en": "Romance", "fa": "عاشقانه"},
    "drama": {"nl": "Drama", "en": "Drama", "fa": "درام"},
    "humour": {"nl": "Humor", "en": "Humour", "fa": "طنز"},
    "mystery": {"nl": "Raadsel", "en": "Mystery", "fa": "معما"},
    "community": {"nl": "Samenleven", "en": "Community", "fa": "زندگی اجتماعی"},
    "reflective": {"nl": "Nadenken", "en": "Reflection", "fa": "تأمل"},
}
INSPIRATIONS = {
    "belgian-daily-life": ["belgium-daily-life"],
    "culture": ["vlaanderen-culture"],
    "public-domain-sketches": ["dbnl-love001nieu01", "dbnl-love002poly01", "dbnl-love002drie01"],
    "public-domain-student-life": ["dbnl-berg062erne01"],
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compile_stage(root: Path, draft: dict, baseline_entries: list[dict] | None = None) -> tuple[dict, dict, list[dict]]:
    stage = draft["stage_id"]
    if stage not in STAGE_IDS or set(draft) - {"stage_id", "new_vocabulary", "core", "stories"}:
        raise ValueError(f"invalid manuscript stage or fields: {stage}")
    base = read(root / "content/library" / f"{stage}.json")
    for folder in ("source-lessons", "learning-units"):
        path = root / "content" / folder / f"{stage}.json"
        if path.exists():
            extra = read(path)
            base["vocabulary"].extend(extra["vocabulary"])
            base["stories"].extend(extra["stories"])
    words = {word["id"]: word for word in base["vocabulary"]}
    terms = {normalise(word["term"]) for word in words.values()}
    new_words = []
    for item in draft.get("new_vocabulary", []):
        word = LibraryWord.model_validate(item)
        if not word.id.startswith(stage + "-core-") or word.id in words or normalise(word.term) in terms:
            raise ValueError(f"duplicate or unbound new word: {word.id}")
        new_words.append(word.model_dump())
        words[word.id] = word.model_dump()
        terms.add(normalise(word.term))
    core = draft["core"]
    core_fields = {"word_id", "term", "part_of_speech", "article", "plural", "forms", "contexts"}
    if any(set(entry) - core_fields for entry in core):
        raise ValueError(f"{stage}: core contains unsupported fields")
    if len(core) != 150 or len({item["word_id"] for item in core}) != 150:
        raise ValueError(f"{stage}: productive core must contain exactly 150 distinct words")
    entries = []
    allowed = STAGE_STRUCTURES.get(stage, ALL_STRUCTURES)
    # Begin with a usable mix rather than making a learner finish 75 nouns
    # before meeting a verb. This changes only display order, never evidence.
    buckets = defaultdict(deque)
    for item in core:
        buckets[item["part_of_speech"]].append(item)
    parts = ("noun", "verb", "adjective", "adverb", "expression", "other")
    if any(pos not in parts for pos in buckets):
        raise ValueError(f"{stage}: unsupported word class in productive core")
    ordered = []
    while any(buckets.values()):
        for pos in parts:
            if buckets[pos]:
                ordered.append(buckets[pos].popleft())
    for position, item in enumerate(ordered, 1):
        entry = deepcopy(item)
        word_id = entry["word_id"]
        if word_id not in words or words[word_id]["term"] != entry["term"]:
            raise ValueError(f"{stage}: core ID and term must match: {word_id}")
        if len(entry.get("contexts", [])) != 3:
            raise ValueError(f"{word_id}: exactly three authored contexts required")
        entry["productive_core"] = True
        entry["core_order"] = position
        for index, context in enumerate(entry["contexts"], 1):
            if context["structure"] not in allowed:
                raise ValueError(f"{word_id}: structure outside stage sequence: {context['structure']}")
            context["id"] = f"{word_id}-core-{index}"
            context["production_prompt"] = PROMPTS[stage]
        value = LibraryWord.model_validate({**words[word_id], **{k: v for k, v in entry.items() if k != "word_id"}})
        words[word_id] = value.model_dump()
        entries.append(entry)
    counts = Counter(entry["part_of_speech"] for entry in entries)
    # Product balance limits, not CEFR word-class prescriptions.
    for pos, minimum in {"noun": 35, "verb": 30, "adjective": 20, "adverb": 15, "expression": 10}.items():
        if counts[pos] < minimum:
            raise ValueError(f"{stage}: insufficient {pos} coverage ({counts[pos]}/{minimum})")
    stories = []
    provenance = []
    for number, raw in enumerate(draft["stories"], 1):
        if set(raw) != {"id", "title", "genre", "inspiration", "plot_key", "lines", "vocabulary_ids", "question"}:
            raise ValueError(f"{stage}: unsupported story fields")
        if not re.fullmatch(r"[a-z0-9-]+", raw["id"]) or len(raw["lines"]) != 10:
            raise ValueError(f"{stage}: story needs a slug and exactly ten authored lines")
        if not raw["plot_key"].strip():
            raise ValueError("each story needs a causal plot synopsis")
        key = f"{stage}-s-reading-{raw['id']}"
        question = raw["question"]
        if set(question) != {"prompt", "answer", "distractor", "explanation"}:
            raise ValueError(f"{key}: unsupported comprehension fields")
        if any(normalise(question["answer"][lang]) == normalise(question["distractor"][lang])
               for lang in ("nl", "en", "fa")):
            raise ValueError(f"{key}: answer and distractor must differ")
        index = number % 2
        options = [question["answer"], question["distractor"]]
        if index:
            options.reverse()
        story = LibraryStory.model_validate({
            "id": key, "title": raw["title"], "topic": CATEGORY, "genre": GENRES[raw["genre"]],
            "paragraphs": [{lang: " ".join(line[lang] for line in raw["lines"][start:start+5])
                            for lang in ("nl", "en", "fa")} for start in (0, 5)],
            "lines": raw["lines"], "vocabulary_ids": raw["vocabulary_ids"],
            "question": {"prompt": question["prompt"], "options": options, "answer_index": index,
                         "explanation": question["explanation"]},
        })
        if not set(story.vocabulary_ids).issubset(words):
            raise ValueError(f"{key}: unknown vocabulary reference")
        stories.append(story.model_dump(exclude_none=True))
        provenance.append({"story_id": key, "stage_id": stage, "work_type": "original_fiction",
                           "inspiration_refs": INSPIRATIONS[raw["inspiration"]],
                           "source_use": "broad_theme_only_no_quotation_or_plot_adaptation",
                           "plot_key": raw["plot_key"], "language_review": "pending"})
    # Preserve the original small word journeys for words outside the new core.
    path = root / "content/vocabulary-transfer" / f"{stage}.json"
    old = baseline_entries if baseline_entries is not None else (read(path)["entries"] if path.exists() else [])
    core_ids = {entry["word_id"] for entry in entries}
    old = [item for item in old if item["word_id"] not in core_ids and not item.get("productive_core")]
    usage = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed", "entries": old + entries}
    addition = {"schema_version": 1, "stage_id": stage, "review_status": "unreviewed",
                "vocabulary": new_words, "stories": stories, "topics": [], "grammar_extensions": []}
    base["vocabulary"] = list(words.values())
    base["stories"].extend(stories)
    StageLibrary.model_validate(base)
    new_ids = {word["id"] for word in new_words}
    covered = {ref for story in stories for ref in story["vocabulary_ids"]}
    if not new_ids.issubset(covered):
        raise ValueError(f"{stage}: new vocabulary lacks a genuine authored-story connection: {sorted(new_ids-covered)}")
    return addition, usage, provenance


@contextmanager
def exclusive_build(root: Path):
    """A process-owned lock also protects shared provenance during partial builds."""
    directory = root / ".local"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "content-expansion.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0, 2)
            if lock.tell() == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError("Another content build is running; retry after it finishes.") from error
        else:
            import fcntl
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError("Another content build is running; retry after it finishes.") from error
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def build(root: Path = ROOT, *, stages: list[str] | None = None, base_entries: dict | None = None) -> dict:
    with exclusive_build(root):
        return _build(root, stages=stages, base_entries=base_entries)


def _build(root: Path, *, stages: list[str] | None, base_entries: dict | None) -> dict:
    paths = sorted((root / "scripts/content_build/expansion").glob("*.json"))
    results = {}
    provenance = []
    existing = root / "content/alignment/story-provenance.json"
    previous = read(existing).get("stories", []) if existing.exists() else []
    for path in paths:
        if stages and path.stem not in stages:
            continue
        draft = read(path)
        if draft["stage_id"] != path.stem:
            raise ValueError("manuscript filename does not match stage")
        for batch_path in sorted((root / "scripts/content_build/expansion-stories" / path.stem).glob("*.json")):
            batch = read(batch_path)
            if set(batch) != {"stage_id", "stories"} or batch["stage_id"] != path.stem:
                raise ValueError("story batch must belong to its manuscript stage")
            draft["stories"].extend(batch["stories"])
        baseline = base_entries.get(path.stem) if base_entries is not None else None
        addition, usage, references = compile_stage(root, draft, baseline)
        results[path.stem] = (addition, usage)
        provenance.extend(references)
    kept = [record for record in previous if record["stage_id"] not in results]
    provenance = kept + provenance
    keys = [normalise(record["plot_key"]) for record in provenance]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate causal plot synopsis across stages")
    # Validate everything before replacing any runtime pack.
    outputs = []
    for stage, (addition, usage) in results.items():
        outputs += [(root / "content/reading-library" / f"{stage}.json", addition),
                    (root / "content/vocabulary-transfer" / f"{stage}.json", usage)]
    outputs.append((root / "content/alignment/story-provenance.json",
                    {"schema_version": 1, "source_registry": "source-registry.json", "stories": provenance}))
    for path, value in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    return {stage: {"core_words": sum(item.get("productive_core", False) for item in usage["entries"]),
                    "new_stories": len(addition["stories"]), "new_cards": len(addition["vocabulary"])}
            for stage, (addition, usage) in results.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="append", choices=STAGE_IDS)
    args = parser.parse_args()
    print(json.dumps(build(stages=args.stage), indent=2))
