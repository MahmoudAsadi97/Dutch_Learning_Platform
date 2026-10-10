"""Items with speech: listen and choose, dictation, and shadowing (repeat after me).

The text an item speaks stays in its key (`audio_text`); the browser fetches the sound from
`POST .../items/{item_id}/audio`, which serves it from the speech cache (a hit costs no allowance). The prompt
never carries the spoken text of listen-and-choose or dictation. Shadowing shows its sentence and asks the
learner to say it; its outcome is only heard or not heard, never a score (D-20, D-23), and it writes no mistake.

The sentences come from the pool (`Pool.dictated`, `Pool.shadowed`). A listened noun is offered among nouns
of its own article where the topic has three, so hearing "het" alone does not give the answer away.
"""
from __future__ import annotations

import random

from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.generators import Draft, distractors, option_ids, word_card
from dlp.domains.exercises.pool import Pool, Word


def _refs(ids: list[str], words: list[Word]) -> dict[str, dict[str, str]]:
    return {"words": {i: w.key for i, w in zip(ids, words, strict=True)},
            "refs": {i: f"word:{w.id}" for i, w in zip(ids, words, strict=True)}}


def listen_choose(pool: Pool, word: Word, rng: random.Random) -> Draft | None:
    """The word is spoken; four written words of its topic to choose from."""
    candidates = pool.choice.get(word.id)
    if not candidates:
        return None
    same = tuple(i for i in candidates if pool.by_id[i].article == word.article) if word.article else ()
    others = (distractors(pool, word, rng, same) if same else None) or distractors(pool, word, rng, candidates)
    if others is None:
        return None
    words = [word, *others]
    rng.shuffle(words)
    ids = option_ids(rng, len(words))
    support = [{"id": i, "nl": w.term, "en": w.meaning["en"], "fa": w.meaning["fa"]}
               for i, w in zip(ids, words, strict=True)]
    return Draft(kind="listen_choose", ref=f"word:{word.id}", word=word.key, skill="listening",
                 words=tuple(w.id for w in words),
                 prompt={"kind": "listen_choose", "options": [{"id": i, "nl": w.term} for i, w in zip(ids, words,
                                                                                                    strict=True)]},
                 key={"answer": ids[words.index(word)], "audio_text": word.term, "support": support,
                      "word": word_card(word), **_refs(ids, words)})


def dictation(pool: Pool, word: Word, *, single: bool = False) -> Draft | None:
    """A sentence of the word's example is spoken and typed (at pre-A1 the word alone)."""
    text = word.term if single else pool.dictated.get(word.id)
    if text is None:
        return None
    # counted the way answers are compared: "e-mail" is one word
    return Draft(kind="dictation", ref=f"word:{word.id}", word=word.key, skill="listening", words=(word.id,),
                 prompt={"kind": "dictation", "word_count": len(fold(text).split())},
                 key={"accepted": [text], "article": "optional" if single and word.article else "none",
                      "audio_text": text, "word": word_card(word),
                      "words": {"answer": word.key}, "refs": {"answer": f"word:{word.id}"}})


def shadow(pool: Pool, word: Word) -> Draft | None:
    """A short sentence of the word's example to hear and say after the voice."""
    text = pool.shadowed.get(word.id)
    if text is None:
        return None
    return Draft(kind="shadow", ref=f"word:{word.id}", word=word.key, skill="speaking", words=(word.id,),
                 prompt={"kind": "shadow", "sentence": text},
                 key={"audio_text": text, "word": word_card(word),
                      "words": {"answer": word.key}, "refs": {"answer": f"word:{word.id}"}})

