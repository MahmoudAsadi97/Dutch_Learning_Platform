"""Facts about the static content that the exercise engine (roadmap P3) builds on, measured per stage.

The recorded table is the measurement of 2026-10-06. A content rebuild that changes it must update the table
on purpose, because the item generators choose kinds per stage from exactly these facts: how many library
words share a topic (match pairs), whether a term appears in its own example (cloze), de/het balance
(article sort), how many examples are short (sentence builder), how many sentences a reading text has
(sentence ordering), and the sentence-frame collisions at A2, pre-B1 and B1 that make sibling words fit the
same cloze (the distractor rule in step 3.3).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

import pytest

from dlp.domains.curriculum.library import library_for
from dlp.domains.curriculum.service import curriculum
from dlp.domains.curriculum.topics import topics_for
from dlp.domains.stories.validator import sentences, tokens

ARTICLE = re.compile(r"^(de|het|een)\s+", re.I)

# stage -> (topic groups, smallest group, terms found in their example, het, de, short examples (3-9 tokens),
#           words sharing a sentence frame, topic groups with a frame collision, reading texts under 3 sentences,
#           smallest topic vocabulary list, option counts of the authored questions)
RECORDED = {
    "pre-a1": (100, 5, 494, 89, 220, 355, 0, 0, 82, 5, {2: 400}),
    "a1": (100, 5, 495, 89, 220, 153, 0, 0, 72, 5, {2: 400}),
    "pre-a2": (100, 5, 496, 89, 220, 7, 0, 0, 82, 5, {2: 400}),
    "a2": (50, 10, 500, 89, 241, 500, 491, 50, 1, 5, {2: 400}),
    "pre-b1": (50, 10, 498, 93, 257, 72, 489, 50, 0, 2, {2: 400}),
    "b1": (50, 10, 497, 93, 257, 0, 488, 50, 1, 1, {2: 400}),
    "pre-b2": (10, 25, 446, 57, 344, 359, 0, 0, 0, 5, {3: 400}),
    "b2": (10, 25, 447, 57, 344, 0, 0, 0, 0, 5, {3: 400}),
    "pre-c1": (10, 25, 446, 57, 344, 0, 0, 0, 0, 5, {3: 400}),
    "c1": (10, 50, 499, 9, 491, 35, 0, 0, 0, 5, {2: 300, 3: 100}),
    "pre-c2": (10, 50, 500, 8, 492, 25, 0, 0, 0, 3, {2: 300, 3: 100}),
    "c2": (10, 50, 499, 13, 487, 26, 0, 0, 0, 3, {2: 300, 3: 100}),
}


def core(term: str) -> str:
    return ARTICLE.sub("", term.strip()).lower()


def frame(example: str, term: str) -> str | None:
    """The example with the term blanked, or None when the term does not occur in it."""
    pattern = re.compile(r"\b" + re.escape(core(term)) + r"\b", re.I)
    if not pattern.search(example):
        return None
    return pattern.sub("___", example, count=1).strip().lower()


def measure(stage_id: str) -> tuple:
    bank = library_for(stage_id)
    topics = topics_for(stage_id)
    groups: dict[str, list] = defaultdict(list)
    for word in bank.vocabulary:
        groups[word.topic.nl].append(word)
    frames = [frame(word.example.nl, word.term) for word in bank.vocabulary]
    counts = Counter(f for f in frames if f)
    collisions = 0
    for group in groups.values():
        found = [f for f in (frame(w.example.nl, w.term) for w in group) if f]
        if len(found) >= 2 and len(set(found)) < len(found):
            collisions += 1
    return (
        len(groups),
        min(len(v) for v in groups.values()),
        sum(1 for f in frames if f),
        sum(1 for w in bank.vocabulary if w.term.lower().startswith("het ")),
        sum(1 for w in bank.vocabulary if w.term.lower().startswith("de ")),
        sum(1 for w in bank.vocabulary if 3 <= len(tokens(w.example.nl)) <= 9),
        sum(n for n in counts.values() if n > 1),
        collisions,
        sum(1 for t in topics.topics if len(sentences(t.reading.text.nl)) < 3),
        min(len(t.vocabulary_ids) for t in topics.topics),
        dict(Counter(len(q.options) for t in topics.topics for skill in ("reading", "listening")
                     for q in getattr(t, skill).questions)),
    )


def test_every_stage_is_recorded():
    assert [stage.id for stage in curriculum().stages] == list(RECORDED)


@pytest.mark.parametrize("stage_id", list(RECORDED))
def test_content_facts_match_the_recorded_table(stage_id):
    measured = measure(stage_id)
    assert measured == RECORDED[stage_id], f"{stage_id}: content changed; re-measure and update RECORDED on purpose"


@pytest.mark.parametrize("stage_id", list(RECORDED))
def test_invariants_the_generators_rely_on(stage_id):
    groups, smallest, found, het, de, _short, _shared, _collisions, _lt3, _vocab_min, options = RECORDED[stage_id]
    assert smallest >= 4, "match pairs need at least four words per library topic"
    assert found >= 440, "cloze needs the term inside its own example for most cards"
    assert groups >= 10
    if stage_id in ("pre-a1", "a1", "pre-a2", "a2", "pre-b1", "b1", "pre-b2", "b2", "pre-c1"):
        assert het >= 50 and de >= 150, "de/het sorting needs both articles at this stage"
    assert all(n in (2, 3) for n in options), "authored questions have two or three options"


def test_frame_collisions_are_confined_to_a2_pre_b1_and_b1():
    """Every topic group at these three stages shares a sentence frame between siblings, so a sibling used as
    a cloze distractor would fit the blank; the generator must refuse those distractors (step 3.3)."""
    for stage_id, row in RECORDED.items():
        collisions = row[7]
        if stage_id in ("a2", "pre-b1", "b1"):
            assert collisions == 50
        else:
            assert collisions == 0
