"""Appending authoring units keeps stable IDs and binds provenance to the complete pack."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy

import pytest

from dlp.config import CONTENT_DIR


@pytest.fixture
def builder(tmp_path):
    source = CONTENT_DIR.parent / "scripts/content_build/source_lessons.py"
    spec = importlib.util.spec_from_file_location("source_lesson_builder", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("library/pre-a1.json", "curriculum/path.json", "source-index/manifest.json", "source-index/stage-map.json"):
        path = tmp_path / "content" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((CONTENT_DIR / name).read_bytes())
    return module, tmp_path


def test_multiple_units_share_targets_and_grammar_without_changing_the_first_unit(builder):
    module, root = builder
    original = deepcopy(module.UNITS[0])
    module.build([original], root)
    path = root / "content/source-lessons/pre-a1.json"
    before = json.loads(path.read_text())
    addition = deepcopy(original)
    addition["unit"] = 2
    module.build([addition, original], root)  # Numbers, rather than source-list order, fix the IDs.
    after = json.loads(path.read_text())
    assert after["topics"][0] == before["topics"][0]
    assert after["stories"][0] == before["stories"][0]
    assert after["vocabulary"] == before["vocabulary"]
    assert after["topics"][1]["id"] == "pre-a1-t-source-02"
    assert after["topics"][1]["vocabulary_ids"] == before["topics"][0]["vocabulary_ids"]
    assert len(after["grammar_extensions"]) == 1
    rule = after["grammar_extensions"][0]
    assert rule["practice"][0] == before["grammar_extensions"][0]["practice"][0]
    assert rule["practice"][1]["id"] == "pre-a1-source-grammar-02"
    links_path = root / "content/source-index/lesson-links.json"
    links = json.loads(links_path.read_text())["lessons"]
    assert len(links) == 2
    assert all(link["pack_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest() for link in links)
    files = (path.read_bytes(), links_path.read_bytes())
    module.build([addition, original], root)
    assert files == (path.read_bytes(), links_path.read_bytes())


@pytest.mark.parametrize("case", ("duplicate-number", "unknown-stage", "unknown-rule", "unknown-concept",
                                  "unmapped-concept", "invalid-number",
                                  "unknown-source", "zero-page", "outside-page", "duplicate-target"))
def test_invalid_authoring_contracts_fail_before_writing_lesson_files(builder, case):
    module, root = builder
    first = deepcopy(module.UNITS[0])
    other = deepcopy(first)
    other["unit"] = 2
    if case == "duplicate-number":
        other["unit"] = 1
    elif case == "unknown-stage":
        other["stage"] = "a3"
    elif case == "unknown-rule":
        other["grammar"] = "not-a-rule"
    elif case == "unknown-concept":
        other["concept"] = "not-a-concept"
    elif case == "unmapped-concept":
        other["concept"] = "spatial-prepositions"
    elif case == "invalid-number":
        other["unit"] = 100
    elif case == "unknown-source":
        other["sources"] = [("source-99", 1)]
    elif case == "zero-page":
        other["sources"] = [("source-01", 0)]
    elif case == "outside-page":
        other["sources"] = [("source-01", 121)]
    elif case == "duplicate-target":
        other["words"][1] = other["words"][0]
    with pytest.raises(ValueError):
        module.build([first, other], root)
    assert not (root / "content/source-lessons").exists()
    assert not (root / "content/source-index/lesson-links.json").exists()
