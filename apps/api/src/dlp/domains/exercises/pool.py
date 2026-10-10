"""The words a stage's exercises are made of, indexed once per library file, and the content gate.

Everything here is read from `content/library/{stage}.json` through `library.library_for` (called through the
module, so tests can swap the bank). Per word it works out what each kind needs: four-option choice
distractors (same topic first, different word, different meaning in every language), and a cloze card when
the term stands exactly once in its own example and no other form of it stands there too ("offertes" next to
the blank for "offerte").

Cloze distractors are siblings from the same topic and article class, never a word with the same meaning or
one already visible in the sentence. Siblings of one topic often fit the same blank (any colour fits "Ik kies
___ voor mijn sjaal", and at A2 to B1 whole topics share one sentence frame, the definition of
tests/test_content_exercise_pool.py), so every cloze card shows the sentence's translation as the cue that
tells them apart (the red-team rule of step 3.3, applied to every card). Where the translation shows the
Dutch word itself (a cognate, "e-mail" as "email"), or fewer than three siblings remain, the word is practised
by choice only.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from dlp.domains.curriculum import library
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.compare import fold, strip_accents
from dlp.domains.exercises.themes import related
from dlp.domains.stories.vocab import key_for

ARTICLE = re.compile(r"^(de|het|een)\s+", re.I)
DISTRACTORS = 3
# choice draws distractors from this many neighbouring topics when a topic is too small
NEIGHBOUR_TOPICS = 4
# odd one out: the odd word comes from a topic at least this far away in the library's topic order, outside
# the group's theme (themes.py)
ODD_TOPIC_DISTANCE = 10
# odd one out only where topics are small situations (pre-A1 to B1); from pre-B2 a topic holds 25-100 words
ODD_ONE_OUT_LAST_STAGE = "b1"
# Dutch definitions as choice options from A2 on
DEFINITION_FIRST_STAGE = "a2"
# The content gate: a stage offers engine sessions only when this many of its words support a four-option
# choice, its examples hold this many distinct sentences, and it supports at least this many kinds with at least
# KIND_MIN_ITEMS items each. Every stage passes on the content of 6 Oct 2026 (tests/test_exercise_generators.py
# records the numbers, with the sentence frames and the share of words new against earlier stages); the gate
# keeps a thin or templated rebuild out. Reused word lists are labelled as review (roadmap 3.9).
VARIETY_MIN_CHOICE_WORDS = 200
VARIETY_MIN_EXAMPLES = 150
VARIETY_MIN_KINDS = 2
KIND_MIN_ITEMS = 50
_TOKEN = re.compile(r"[^\W\d_]+", re.UNICODE)


@dataclass(frozen=True)
class Word:
    id: str
    term: str
    core: str  # the term without its article, lower case: what fills a cloze blank
    article: str  # de, het, een or ''
    key: str  # the same word across stages (stories.vocab.key_for)
    order: int  # position in the library
    topic: str  # topic.nl
    topic_index: int
    topic_label: dict[str, str]
    meaning: dict[str, str]
    example: dict[str, str]
    frame: str | None  # the example with the term blanked, lower case
    span: tuple[int, int] | None  # where the term stands in example.nl, when it stands there alone
    senses: frozenset[str]  # its meaning in nl, en and fa, normalised


@dataclass(frozen=True)
class ClozeCard:
    sentence: str  # example.nl with the term blanked; the translation is always the cue
    distractors: tuple[str, ...]  # word ids


@dataclass(frozen=True)
class Variety:
    words: int
    choice: int  # words with a four-option choice
    cloze: int  # cloze cards
    odd_one_out: int  # topics an odd-one-out item can be built from
    examples: int  # distinct example sentences
    frames: int  # distinct sentence frames (examples with their word blanked)
    kinds: tuple[str, ...]  # kinds with at least KIND_MIN_ITEMS items

    @property
    def enabled(self) -> bool:
        return (self.choice >= VARIETY_MIN_CHOICE_WORDS and self.examples >= VARIETY_MIN_EXAMPLES
                and len(self.kinds) >= VARIETY_MIN_KINDS)


@dataclass(frozen=True)
class Pool:
    stage_id: str
    content_version: str
    words: tuple[Word, ...]
    by_id: dict[str, Word]
    topics: tuple[str, ...]
    by_topic: dict[str, tuple[Word, ...]]
    choice: dict[str, tuple[str, ...]]  # word id -> distractor candidates, same topic first
    cloze: dict[str, ClozeCard]
    odd_one_out: bool
    definitions: bool
    variety: Variety = field(init=False)

    def __post_init__(self) -> None:
        odd = sum(1 for topic in self.topics if len(self.by_topic[topic]) >= 3 and self.far_topics(topic))
        counts = (("choice", len(self.choice)), ("cloze_choice", len(self.cloze)),
                  ("odd_one_out", odd if self.odd_one_out else 0))
        object.__setattr__(self, "variety", Variety(
            words=len(self.words), choice=len(self.choice), cloze=len(self.cloze),
            odd_one_out=odd if self.odd_one_out else 0,
            examples=len({word.example["nl"] for word in self.words}),
            frames=len({word.frame for word in self.words if word.frame}),
            kinds=tuple(kind for kind, count in counts if count >= KIND_MIN_ITEMS)))

    def far_topics(self, topic: str) -> tuple[str, ...]:
        """Topics an odd word may come from: far down or up the list, and not the same theme."""
        index = self.topics.index(topic)
        return tuple(other for i, other in enumerate(self.topics)
                     if abs(i - index) >= ODD_TOPIC_DISTANCE and not related(topic, other))


def core(term: str) -> str:
    return ARTICLE.sub("", term.strip()).lower()


def word_pattern(text: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(text) + r"\b", re.I)


def contains_word(text: str, word: str) -> bool:
    """`word` stands in `text` as a word or the start of one ("voetbal" in "voetbal speelt", "koffie" in
    "koffiebonen"); accents and case aside."""
    return re.search(r"\b" + re.escape(strip_accents(word.lower())), strip_accents(fold(text))) is not None


def _different(a: Word, b: Word) -> bool:
    """Two words a learner can tell apart: another word, and another meaning in every language."""
    return a.key != b.key and a.core != b.core and not a.senses & b.senses


def _span(example: str, term_core: str) -> tuple[int, int] | None:
    """Where the term stands, when it stands there once and no other form of it does ("offertes", "kortere",
    "begrijp" for "begrijpen")."""
    found = list(word_pattern(term_core).finditer(example)) if term_core else []
    if len(found) != 1:
        return None
    start, end = found[0].span()
    stem = term_core[:-2] if term_core.endswith("en") and len(term_core) > 5 else term_core
    rest = example[:start] + " " + example[end:]
    if any(token.lower().startswith(stem) for token in _TOKEN.findall(rest)) and " " not in term_core:
        return None
    return start, end


def _word(item, order: int, topic_index: int) -> Word:
    term_core = core(item.term)
    match = ARTICLE.match(item.term.strip())
    pattern = word_pattern(term_core)
    frame = pattern.sub("___", item.example.nl, count=1).strip().lower() if term_core and pattern.search(
        item.example.nl) else None
    return Word(id=item.id, term=item.term, core=term_core, article=match.group(1).lower() if match else "",
                key=key_for(item.term), order=order, topic=item.topic.nl, topic_index=topic_index,
                topic_label=item.topic.model_dump(), meaning=item.meaning.model_dump(),
                example=item.example.model_dump(), frame=frame, span=_span(item.example.nl, term_core),
                senses=frozenset(library.normalise(text) for text in (item.meaning.nl, item.meaning.en,
                                                                       item.meaning.fa)))


def _squash(text: str) -> str:
    return strip_accents(text).replace("-", "").replace("'", "").replace(" ", "")


def gives_away(word: Word) -> bool:
    """The translation shows the Dutch word itself: a cognate or a name, also written as one word, two words or
    without its hyphen ("email" for "e-mail", "yoga mat" for "yogamat")."""
    target = _squash(word.core)
    width = max(3, len(word.core.split()) + 1)
    for lang in ("en", "fa"):
        tokens = strip_accents(fold(word.example[lang])).split()
        for start in range(len(tokens)):
            for size in range(1, width + 1):
                if _squash("".join(tokens[start:start + size])) == target:
                    return True
    return False


def _cloze(word: Word, siblings: tuple[Word, ...], patterns: dict[str, re.Pattern[str]]) -> ClozeCard | None:
    if word.span is None or gives_away(word):
        return None
    start, end = word.span
    fitting = tuple(other.id for other in siblings
                    if other.id != word.id and other.article == word.article and _different(word, other)
                    and not patterns[other.id].search(word.example["nl"]))
    if len(fitting) < DISTRACTORS:
        return None
    return ClozeCard(sentence=word.example["nl"][:start] + "___" + word.example["nl"][end:], distractors=fitting)


def build(bank) -> Pool:
    topics: list[str] = []
    for item in bank.vocabulary:
        if item.topic.nl not in topics:
            topics.append(item.topic.nl)
    words = tuple(_word(item, order, topics.index(item.topic.nl)) for order, item in enumerate(bank.vocabulary))
    by_topic = {topic: tuple(word for word in words if word.topic == topic) for topic in topics}
    neighbours = {topic: sorted((i for i in range(len(topics)) if i != index), key=lambda i: (abs(i - index), i))
                  [:NEIGHBOUR_TOPICS] for index, topic in enumerate(topics)}
    patterns = {word.id: word_pattern(word.core) for word in words}
    choice: dict[str, tuple[str, ...]] = {}
    cloze: dict[str, ClozeCard] = {}
    for word in words:
        nearby = [*by_topic[word.topic], *(w for i in neighbours[word.topic] for w in by_topic[topics[i]])]
        candidates = tuple(other.id for other in nearby if other.id != word.id and _different(word, other))
        if len(candidates) >= DISTRACTORS:
            choice[word.id] = candidates
        card = _cloze(word, by_topic[word.topic], patterns)
        if card:
            cloze[word.id] = card
    stage_index = STAGE_IDS.index(bank.stage_id)
    return Pool(
        stage_id=bank.stage_id,
        content_version=hashlib.sha256(bank.model_dump_json().encode()).hexdigest(),
        words=words, by_id={word.id: word for word in words}, topics=tuple(topics), by_topic=by_topic,
        choice=choice, cloze=cloze,
        odd_one_out=stage_index <= STAGE_IDS.index(ODD_ONE_OUT_LAST_STAGE),
        definitions=stage_index >= STAGE_IDS.index(DEFINITION_FIRST_STAGE),
    )


_POOLS: dict[str, tuple[object, Pool]] = {}


def pool_for(stage_id: str) -> Pool:
    """The stage's pool, rebuilt when the library file (or a test's bank) changes."""
    bank = library.library_for(stage_id)
    cached = _POOLS.get(stage_id)
    if cached and cached[0] is bank:
        return cached[1]
    pool = build(bank)
    _POOLS[stage_id] = (bank, pool)
    return pool
