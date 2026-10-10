"""Which words of a text were recognised when the learner read it aloud.

The speech service hears words, not pronunciation, and hesitant speech is often misheard; so this counts
recognised words, lists the ones it did not hear, and never turns that into a score (D-20, D-23).
"""
from __future__ import annotations

from dlp.domains.stories.validator import tokens
from dlp.errors import DomainError


def require_words(text: str) -> None:
    """Refuse a text with nothing to compare (only spaces, punctuation or digits) before any audio is paid for."""
    if not tokens(text):
        raise DomainError("the text has no words to read aloud", 422, code="nothing_to_read")


def read_aloud_compare(target: str, transcript: str) -> dict:
    expected = tokens(target)
    remaining = tokens(transcript)
    matched = 0
    missed: list[str] = []
    for word in expected:
        if word in remaining:
            remaining.remove(word)
            matched += 1
        else:
            missed.append(word)
    return {"target_words": len(expected), "matched_words": matched, "missed": missed[:40], "extra": remaining[:40]}
