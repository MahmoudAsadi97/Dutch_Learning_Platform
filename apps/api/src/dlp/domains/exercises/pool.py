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

For the kinds of step 3.4 it also keeps the stage's terms (the real-word guard of typed answers), a sentence
of each word's example cut into tiles or chunks (sentences.py), the nouns that can be sorted into de and het
(up to pre-C1, where nearly every noun is de from C1 on; never a noun that takes both articles), and runs of
three or four sentences from the Story Time paragraphs to put back in order (pre-B1 and from pre-B2; the
paragraphs of the other stages are too short).

For the kinds with speech (step 3.5) it keeps the sentence of each example that holds the word, without a
number or a quotation, when it is short enough to say after the voice (shadowing, three to ten words) or to
type from hearing (dictation, three to twelve). A dictated sentence has no name in it either, since a name's
spelling cannot be heard. B1's examples are nearly all longer, so B1 has no shadowing yet (generated
sentences for the thin stages come with roadmap 7.9).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from dlp.domains.curriculum import library
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises import sentences as cutting
from dlp.domains.exercises.compare import fold, strip_accents
from dlp.domains.exercises.themes import related
from dlp.domains.stories.validator import sentences
from dlp.domains.stories.vocab import key_for

ARTICLE = re.compile(r"^(de|het|een)\s+", re.I)
DISTRACTORS = 3
# words in a sentence to say after the voice, and in one to type from hearing
SHADOW_WORDS = (3, 10)
DICTATION_WORDS = (3, 12)
_DIGIT = re.compile(r"\d")
_QUOTE = re.compile(r"[\"“”„«»]")  # not ’, the apostrophe of ’s morgens
# choice draws distractors from this many neighbouring topics when a topic is too small
NEIGHBOUR_TOPICS = 4
# odd one out: the odd word comes from a topic at least this far away in the library's topic order, outside
# the group's theme (themes.py)
ODD_TOPIC_DISTANCE = 10
# odd one out only where topics are small situations (pre-A1 to B1); from pre-B2 a topic holds 25-100 words
ODD_ONE_OUT_LAST_STAGE = "b1"
# Dutch definitions as choice options from A2 on
DEFINITION_FIRST_STAGE = "a2"
# de/het sorting up to pre-C1; from C1 98% of the nouns take de
DE_HET_LAST_STAGE = "pre-c1"
# putting sentences back in order from pre-B1 (B1's paragraphs happen to be too short: it has none)
ORDER_FIRST_STAGE = "pre-b1"
# nouns whose article changes with the meaning (het punt / de punt, het pad / de pad) or that take both (de/het
# matras): sorting them into one bin would mark right Dutch wrong
DOUBLE_ARTICLE = frozenset({
    "punt", "pad", "bal", "doek", "bos", "rooster", "band", "lid", "stof", "veer", "blik", "hof", "jacht", "portier",
    "matras", "aanrecht", "kauwgom", "filter", "deksel", "soort", "idee", "patroon", "schot", "slot", "vorst",
    "pijp", "bot", "kamp", "loods", "veld", "vat",
})
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
    order: int  # learning priority: the productive core, then the wider library
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
class Pieces:
    """A sentence of a word's example as tiles (short) or chunks (long), in the right order."""
    pieces: tuple[str, ...]
    end: str  # the final punctuation, shown after the pieces
    sentence: str
    cue: dict[str, str] | None  # the sentence's translation, when the translation splits into the same sentences


@dataclass(frozen=True)
class OrderRun:
    ref: str  # story:<story id>:<paragraph>
    sentences: tuple[str, ...]
    translation: dict[str, tuple[str, ...]]  # en/fa, when the translation splits into the same sentences
    words: frozenset[str]  # the story's vocabulary ids


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
    lexicon: frozenset[str] = frozenset()  # every term of the stage, for the real-word guard of typed answers
    pieces: dict[str, Pieces] = field(default_factory=dict)  # word id -> a sentence for the sentence builder
    sortable: tuple[str, ...] = ()  # word ids of nouns to sort into de and het
    orders: tuple[OrderRun, ...] = ()
    shadowed: dict[str, str] = field(default_factory=dict)  # word id -> a sentence to say after the voice
    dictated: dict[str, str] = field(default_factory=dict)  # word id -> a sentence to type from hearing
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

    def available(self) -> dict[str, int]:
        """How many items or cards each kind has at this stage (the availability matrix of step 3.4)."""
        typed = sum(1 for word in self.words if word.span and not gives_away(word))
        recall = sum(1 for word in self.words if not gives_away(word, word.meaning))
        return {"choice": len(self.choice), "cloze_choice": len(self.cloze), "cloze_typed": typed,
                "typed_recall": recall, "flashcard": len(self.words), "match_pairs": len(self.choice),
                "de_het": len(self.sortable), "sentence_builder": len(self.pieces), "sentence_order": len(self.orders),
                "odd_one_out": self.variety.odd_one_out, "listen_choose": len(self.choice),
                "dictation": len(self.dictated), "shadow": len(self.shadowed)}

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


def gives_away(word: Word, texts: dict[str, str] | None = None) -> bool:
    """The translation (of the example, or the given texts such as the meaning) shows the Dutch word itself: a
    cognate or a name, also written as one word, two words or without its hyphen ("email" for "e-mail", "yoga
    mat" for "yogamat", "bed" for "het bed")."""
    texts = texts if texts is not None else word.example
    target = _squash(word.core)
    width = max(3, len(word.core.split()) + 1)
    for lang in ("en", "fa"):
        tokens = strip_accents(fold(texts[lang])).split()
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


def _aligned(text: dict[str, str], index: int, count: int) -> dict[str, str] | None:
    """The translation of sentence `index` of `count`, in the languages that split the same way."""
    found = {lang: parts[index] for lang in ("en", "fa")
             if len(parts := sentences(text[lang])) == count}
    return found or None


def _pieces(word: Word, lower: frozenset[str]) -> Pieces | None:
    parts = sentences(word.example["nl"])
    for index, part in enumerate(parts):
        if not word_pattern(word.core).search(part):
            continue
        cut = cutting.tiles(part, lower) or cutting.chunks(part, lower)
        if cut:
            return Pieces(pieces=tuple(cut[0]), end=cut[1], sentence=part,
                          cue=_aligned(word.example, index, len(parts)))
    return None


def _sortable(words: tuple[Word, ...]) -> tuple[str, ...]:
    """Single-word nouns whose article is not in doubt (no other term of the stage gives it the other one)."""
    articles: dict[str, set[str]] = {}
    for word in words:
        articles.setdefault(word.core, set()).add(word.article)
    return tuple(word.id for word in words if word.article in ("de", "het") and " " not in word.core
                 and articles[word.core] == {word.article} and word.core not in DOUBLE_ARTICLE)


def _orders(bank) -> tuple[OrderRun, ...]:
    runs: list[OrderRun] = []
    for story in getattr(bank, "stories", ()):
        for index, paragraph in enumerate(story.paragraphs):
            run = cutting.order_run(paragraph.nl)
            if run is None:
                continue
            count = len(sentences(paragraph.nl))
            translation = {lang: tuple(parts[: len(run)]) for lang in ("en", "fa")
                           if len(parts := sentences(getattr(paragraph, lang))) == count}
            runs.append(OrderRun(ref=f"story:{story.id}:{index}", sentences=tuple(run), translation=translation,
                                 words=frozenset(story.vocabulary_ids)))
    return tuple(runs)


def _named(sentence: str, lower: frozenset[str]) -> bool:
    """A capitalised word the stage never writes in lower case: a name ("Mina", "Gent")."""
    words = [word for word in (w.strip(".,!?;:\"“”‘’()…") for w in sentence.split()) if word]
    return any(word[:1].isupper() and word.lower() not in lower for word in words)


def _spoken(word: Word, bounds: tuple[int, int], lower: frozenset[str], *, names: bool) -> str | None:
    """The sentence of the word's example that holds the word, when it is short enough and has no number and no
    quotation (a sentence cut inside one would be half of it)."""
    for part in sentences(word.example["nl"]):
        if (word_pattern(word.core).search(part) and bounds[0] <= len(fold(part).split()) <= bounds[1]
                and not _DIGIT.search(part) and not _QUOTE.search(part)
                and (names or not _named(part, lower))):
            return part
    return None


def build(bank) -> Pool:
    topics: list[str] = []
    for item in bank.vocabulary:
        if item.topic.nl not in topics:
            topics.append(item.topic.nl)
    indexed = list(enumerate(bank.vocabulary))
    indexed.sort(key=lambda pair: (0, pair[1].core_order) if getattr(pair[1], "productive_core", False)
                 else (1, pair[0]))
    words = tuple(_word(item, order, topics.index(item.topic.nl)) for order, (_, item) in enumerate(indexed))
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
    stories = [paragraph.nl for story in getattr(bank, "stories", ()) for paragraph in story.paragraphs]
    lower = cutting.lower_words([*(word.example["nl"] for word in words), *stories])
    return Pool(
        stage_id=bank.stage_id,
        content_version=hashlib.sha256(bank.model_dump_json().encode()).hexdigest(),
        words=words, by_id={word.id: word for word in words}, topics=tuple(topics), by_topic=by_topic,
        choice=choice, cloze=cloze,
        odd_one_out=stage_index <= STAGE_IDS.index(ODD_ONE_OUT_LAST_STAGE),
        definitions=stage_index >= STAGE_IDS.index(DEFINITION_FIRST_STAGE),
        lexicon=frozenset(word.term for word in words),
        pieces={word.id: found for word in words if (found := _pieces(word, lower))},
        sortable=_sortable(words) if stage_index <= STAGE_IDS.index(DE_HET_LAST_STAGE) else (),
        orders=_orders(bank) if stage_index >= STAGE_IDS.index(ORDER_FIRST_STAGE) else (),
        shadowed={word.id: found for word in words if (found := _spoken(word, SHADOW_WORDS, lower, names=True))},
        dictated={word.id: found for word in words
                  if (found := _spoken(word, DICTATION_WORDS, lower, names=False))},
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
