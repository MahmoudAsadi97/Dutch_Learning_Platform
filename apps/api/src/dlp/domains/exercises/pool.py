"""The words a stage's exercises are made of, indexed once per library file, and the content gate.

Everything here is read from `content/library/{stage}.json` through `library.library_for` (called through the
module, so tests can swap the bank). Per word it works out what each kind needs: four-option choice
distractors (same topic first, different word, different meaning in every language), and a cloze card when
the term stands exactly once in its own example.

The cloze distractor rule (red team, step 3.3): a sibling is illegal when its own example equals the target
sentence with it filled in, i.e. the two share a sentence frame (the definition of
tests/test_content_exercise_pool.py, which records where this happens: A2, pre-B1 and B1). A sibling with the
same meaning, of another article class, or already visible in the sentence is never offered either. With
fewer than three legal distractors the card shows the sentence's translation as a cue, which tells the
siblings apart; when even that leaves fewer than three, or the translation gives the word away, the word is
practised by choice only.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from dlp.domains.curriculum import library
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises.compare import fold, strip_accents
from dlp.domains.stories.vocab import key_for

ARTICLE = re.compile(r"^(de|het|een)\s+", re.I)
DISTRACTORS = 3
# choice draws distractors from this many neighbouring topics when a topic is too small
NEIGHBOUR_TOPICS = 4
# odd one out: the odd word comes from a topic at least this far away in the library's topic order
ODD_TOPIC_DISTANCE = 10
# odd one out only where topics are small situations (pre-A1 to B1); from pre-B2 a topic holds 25-100 words
ODD_ONE_OUT_LAST_STAGE = "b1"
# Dutch definitions as choice options from A2 on
DEFINITION_FIRST_STAGE = "a2"
# The content gate: a stage offers engine sessions only when this many of its words support a four-option
# choice and its words support at least this many kinds. Every stage passes on the content of 6 Oct 2026
# (tests/test_exercise_generators.py records the numbers); the gate keeps a thinner rebuild out.
VARIETY_MIN_CHOICE_WORDS = 200
VARIETY_MIN_KINDS = 2


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
    span: tuple[int, int] | None  # where the term stands in example.nl, when it stands there exactly once
    senses: frozenset[str]  # its meaning in nl, en and fa, normalised


@dataclass(frozen=True)
class ClozeCard:
    sentence: str  # example.nl with the term blanked
    distractors: tuple[str, ...]  # word ids
    cued: bool  # the translation is shown, because siblings fit the sentence too


@dataclass(frozen=True)
class Variety:
    words: int
    choice: int  # words with a four-option choice
    cloze: int
    cloze_cued: int
    odd_one_out: int  # topics an odd-one-out item can be built from
    kinds: tuple[str, ...]

    @property
    def enabled(self) -> bool:
        return self.choice >= VARIETY_MIN_CHOICE_WORDS and len(self.kinds) >= VARIETY_MIN_KINDS


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
        kinds = tuple(kind for kind, count in (("choice", len(self.choice)), ("cloze_choice", len(self.cloze)),
                                               ("odd_one_out", odd if self.odd_one_out else 0)) if count)
        object.__setattr__(self, "variety", Variety(
            words=len(self.words), choice=len(self.choice), cloze=sum(not c.cued for c in self.cloze.values()),
            cloze_cued=sum(c.cued for c in self.cloze.values()), odd_one_out=odd if self.odd_one_out else 0,
            kinds=kinds))

    def far_topics(self, topic: str) -> tuple[str, ...]:
        index = self.topics.index(topic)
        return tuple(other for i, other in enumerate(self.topics) if abs(i - index) >= ODD_TOPIC_DISTANCE)


def core(term: str) -> str:
    return ARTICLE.sub("", term.strip()).lower()


def _pattern(text: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(text) + r"\b", re.I)


def _different(a: Word, b: Word) -> bool:
    """Two words a learner can tell apart: another word, and another meaning in every language."""
    return a.key != b.key and a.core != b.core and not a.senses & b.senses


def _word(item, order: int, topic_index: int) -> Word:
    term_core = core(item.term)
    match = ARTICLE.match(item.term.strip())
    pattern = _pattern(term_core)
    found = list(pattern.finditer(item.example.nl)) if term_core else []
    frame = pattern.sub("___", item.example.nl, count=1).strip().lower() if found else None
    return Word(id=item.id, term=item.term, core=term_core, article=match.group(1).lower() if match else "",
                key=key_for(item.term), order=order, topic=item.topic.nl, topic_index=topic_index,
                topic_label=item.topic.model_dump(), meaning=item.meaning.model_dump(),
                example=item.example.model_dump(), frame=frame,
                span=(found[0].start(), found[0].end()) if len(found) == 1 else None,
                senses=frozenset(library.normalise(text) for text in (item.meaning.nl, item.meaning.en,
                                                                       item.meaning.fa)))


def _gives_away(word: Word) -> bool:
    """The translation shows the Dutch word itself (a cognate or a name)."""
    target = _pattern(strip_accents(word.core))
    return any(target.search(strip_accents(fold(word.example[lang]))) for lang in ("en", "fa"))


def _cloze(word: Word, siblings: tuple[Word, ...], patterns: dict[str, re.Pattern[str]]) -> ClozeCard | None:
    if word.span is None:
        return None
    start, end = word.span
    sentence = word.example["nl"][:start] + "___" + word.example["nl"][end:]
    fitting = [other for other in siblings
               if other.id != word.id and other.article == word.article and _different(word, other)
               and not patterns[other.id].search(word.example["nl"])]
    legal = [other.id for other in fitting if other.frame != word.frame]
    if len(legal) >= DISTRACTORS:
        return ClozeCard(sentence=sentence, distractors=tuple(legal), cued=False)
    if len(fitting) >= DISTRACTORS and not _gives_away(word):
        return ClozeCard(sentence=sentence, distractors=tuple(other.id for other in fitting), cued=True)
    return None


def build(bank) -> Pool:
    topics: list[str] = []
    for item in bank.vocabulary:
        if item.topic.nl not in topics:
            topics.append(item.topic.nl)
    words = tuple(_word(item, order, topics.index(item.topic.nl)) for order, item in enumerate(bank.vocabulary))
    by_topic = {topic: tuple(word for word in words if word.topic == topic) for topic in topics}
    neighbours = {topic: sorted((i for i in range(len(topics)) if i != index), key=lambda i: (abs(i - index), i))
                  [:NEIGHBOUR_TOPICS] for index, topic in enumerate(topics)}
    patterns = {word.id: _pattern(word.core) for word in words}
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
