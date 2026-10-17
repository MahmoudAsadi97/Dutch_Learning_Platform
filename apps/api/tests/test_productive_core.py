"""A selected core is authored practice, not automatically a reviewed or mastered level."""
from __future__ import annotations

import importlib.util
import json
import os
from collections import Counter
from copy import deepcopy

import pytest
from pydantic import ValidationError

from dlp.config import CONTENT_DIR
from dlp.domains.curriculum import library
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.pool import pool_for


def manuscript(stage):
    path = CONTENT_DIR.parent / "scripts/content_build/expansion" / f"{stage}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def compiler():
    source = CONTENT_DIR.parent / "scripts/content_build/compile_expansion.py"
    spec = importlib.util.spec_from_file_location("expansion_test_compiler", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("stage", STAGE_IDS)
def test_stage_has_ordered_balanced_core_with_three_real_examples(stage):
    bank = library.library_for(stage)
    core = [word for word in bank.vocabulary if word.productive_core]
    assert len(core) == 150
    assert {word.core_order for word in core} == set(range(1, 151))
    classes = Counter(word.part_of_speech for word in core)
    for pos, minimum in {"noun": 35, "verb": 30, "adjective": 20, "adverb": 15, "expression": 10}.items():
        assert classes[pos] >= minimum
    for word in core:
        assert len(word.contexts) == 3
        assert len({context.setting.nl for context in word.contexts}) >= 2
        assert len({library.normalise(context.sentence.nl) for context in word.contexts}) == 3
    assert library.summary(bank)["productive_core_count"] == 150
    assert sum(topic["productive_core_count"] for topic in library.summary(bank)["topics"]) == 150
    page = library.vocabulary_page(bank, core_only=True, limit=20)
    assert page["total"] == 150
    assert [word["core_order"] for word in page["items"]] == list(range(1, 21))
    assert {word["part_of_speech"] for word in page["items"]} >= {
        "noun", "verb", "adjective", "adverb", "expression"}
    assert library.vocabulary_page(bank)["total"] >= 500
    assert bank.review_status == "unreviewed"


def test_core_metadata_cannot_create_an_incomplete_or_duplicate_learning_order():
    bank = library.library_for("pre-a1")
    word = next(word for word in bank.vocabulary if word.productive_core).model_dump()
    for change in ({"core_order": None}, {"productive_core": False}, {"contexts": word["contexts"][:2]},
                   {"core_order": 151}, {"part_of_speech": None}):
        with pytest.raises(ValidationError):
            library.LibraryWord.model_validate({**word, **change})
    data = bank.model_dump()
    core = [word for word in data["vocabulary"] if word["productive_core"]]
    core[1]["core_order"] = core[0]["core_order"]
    with pytest.raises(ValidationError, match="positions must be unique"):
        library.StageLibrary.model_validate(data)


def test_source_registry_is_specific_about_editions_and_does_not_claim_endorsement():
    registry = json.loads((CONTENT_DIR / "alignment/source-registry.json").read_text())
    sources = {source["id"]: source for source in registry["sources"]}
    assert all(source["url"].startswith("https://") and source["endorsement"] is False for source in sources.values())
    for key in ("dbnl-love001nieu01", "dbnl-love002poly01", "dbnl-love002drie01", "dbnl-berg062erne01"):
        assert "gebruiksvoorwaarden.php?id=" in sources[key]["rights_url"]
    assert sources["vrt-terms"]["role"] == "excluded_automated_content_source"
    provenance = json.loads((CONTENT_DIR / "alignment/story-provenance.json").read_text())["stories"]
    assert provenance
    assert len({item["story_id"] for item in provenance}) == len(provenance)
    assert len({library.normalise(item["plot_key"]) for item in provenance}) == len(provenance)
    for item in provenance:
        assert item["work_type"] == "original_fiction" and item["language_review"] == "pending"
        assert item["source_use"] == "broad_theme_only_no_quotation_or_plot_adaptation"
        assert set(item["inspiration_refs"]).issubset(sources)
        story = library.story_detail(library.library_for(item["stage_id"]), item["story_id"])
        assert len(story["lines"]) == 10
        assert len(story["paragraphs"]) == 2


def test_compiler_refuses_fake_counts_duplicate_terms_and_approval_fields():
    module = compiler()
    draft = manuscript("pre-a1")
    for kind in ("missing-word", "duplicate-core", "duplicate-card", "invented-review",
                 "core-meaning", "core-id", "core-topic", "core-unknown"):
        bad = deepcopy(draft)
        if kind == "missing-word":
            bad["core"].pop()
        elif kind == "duplicate-core":
            bad["core"][1] = deepcopy(bad["core"][0])
        elif kind == "duplicate-card":
            bad["new_vocabulary"].append(deepcopy(bad["new_vocabulary"][0]))
        elif kind.startswith("core-"):
            bad["core"][0][kind.removeprefix("core-")] = "unsupported override"
        else:
            bad["review_status"] = "approved"
        with pytest.raises(ValueError):
            module.compile_stage(CONTENT_DIR.parent, bad)


def test_new_reading_library_cache_tracks_edits_and_deletion(tmp_path):
    from dlp.domains.curriculum import supplements
    folder = tmp_path / "reading-library"
    folder.mkdir()
    path = folder / "pre-a1.json"
    data = json.loads((CONTENT_DIR / "reading-library/pre-a1.json").read_text())
    path.write_text(json.dumps(data))
    before = supplements.stamp(tmp_path, "pre-a1")
    original_stat = path.stat()
    first_id = data["stories"][0]["id"]
    assert supplements.load(tmp_path, "pre-a1")["stories"][0]["id"] == first_id
    data["stories"][0]["title"]["nl"] = "Een andere titel voor deze cachetest"
    path.write_text(json.dumps(data))
    os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    assert supplements.stamp(tmp_path, "pre-a1") != before
    assert supplements.load(tmp_path, "pre-a1")["stories"][0]["title"]["nl"] == data["stories"][0]["title"]["nl"]
    path.unlink()
    assert not supplements.load(tmp_path, "pre-a1")["stories"]


def test_compiler_prevents_parallel_provenance_writes_and_releases_failed_builds(tmp_path):
    module = compiler()
    with module.exclusive_build(tmp_path):
        with pytest.raises(RuntimeError, match="Another content build"):
            module.build(tmp_path)
    # An exception does not leave an owned lock behind.
    with pytest.raises(ValueError):
        with module.exclusive_build(tmp_path):
            raise ValueError("authoring rejected")
    with module.exclusive_build(tmp_path):
        pass


def test_core_cannot_relabel_three_same_situations_as_transfer():
    bank = library.library_for("pre-a1")
    word = next(word for word in bank.vocabulary if word.productive_core).model_dump()
    for context in word["contexts"]:
        context["setting"] = {"nl": "Dezelfde situatie", "en": "The same situation", "fa": "همان موقعیت"}
    with pytest.raises(ValidationError, match="different communicative situations"):
        library.LibraryWord.model_validate(word)


@pytest.mark.parametrize("stage", STAGE_IDS)
def test_practice_engine_prioritises_the_same_mixed_core_as_the_word_library(stage):
    bank = library.library_for(stage)
    expected = library.vocabulary_page(bank, core_only=True, limit=150)["items"]
    pool = pool_for(stage)
    assert [word.id for word in pool.words[:150]] == [word["id"] for word in expected]
    assert len({word["part_of_speech"] for word in expected[:5]}) == 5
