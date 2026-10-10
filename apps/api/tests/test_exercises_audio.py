"""Exercises with speech (roadmap 3.5): a cached synthesis costs no allowance, prompts never carry the spoken
text, and shadowing is heard or not heard, never a score or a mistake."""
from __future__ import annotations

import json
import random
import uuid
from dataclasses import replace

from sqlalchemy import func, select

from dlp.api.deps import providers_dep
from dlp.db.session import session_scope
from dlp.domains.exercises import audio, blueprints
from dlp.domains.exercises.models import ExerciseItem, LearnerMistake
from dlp.domains.exercises.pool import pool_for
from dlp.domains.identity.models import Learner
from dlp.domains.speech.service import TTS_CACHE_PREFIX, synthesize_cached, tts_cache_key
from dlp.domains.usage.service import snapshot
from dlp.providers.fixtures import FixtureSpeechToText, FixtureTextToSpeech, MemoryBlobStore, tone_wav
from dlp.providers.registry import get_providers
from tests.conftest import auth_headers

SPEECH = {"listen_choose", "dictation", "shadow"}


def _learner(email: str):
    with session_scope() as session:
        learner = Learner(subject=f"fixture:{email}", email=email)
        session.add(learner)
        session.flush()
        return learner.id


def _audio_used(learner_id, settings) -> float:
    with session_scope() as session:
        return snapshot(session, settings, learner_id)["counters"]["audio_seconds"]["daily"]["used"]


def test_a_second_request_for_the_same_text_is_free(database, settings):
    learner_id, other = _learner("tts-cache-1@example.com"), _learner("tts-cache-2@example.com")
    tts, blob = FixtureTextToSpeech(), MemoryBlobStore()
    with session_scope() as session:
        first, hit = synthesize_cached(session, settings, learner_id=learner_id, request_id="tts-cache-0001",
                                       text="Ik neem de  bus.", tts=tts, blob=blob)
    assert not hit and _audio_used(learner_id, settings) > 0
    with session_scope() as session:
        again, hit = synthesize_cached(session, settings, learner_id=other, request_id="tts-cache-0002",
                                       text="Ik neem de bus.", tts=tts, blob=blob)
    assert hit and again == first, "spacing aside, the same course text is the same sound"
    assert _audio_used(other, settings) == 0, "a cache hit costs no allowance"
    key = tts_cache_key(tts, "Ik neem de bus.")
    assert key.startswith(f"{TTS_CACHE_PREFIX}/fixture/") and str(learner_id) not in key, "no learner in the key"


def test_prompts_never_carry_the_spoken_text():
    for stage_id in ("pre-a1", "a2", "b2"):
        stage = pool_for(stage_id)
        for word in stage.words[:120]:
            for draft in (audio.listen_choose(stage, word, random.Random(word.id)),
                          audio.dictation(stage, word, single=stage_id == "pre-a1")):
                if draft is None:
                    continue
                prompt = json.dumps(draft.prompt, ensure_ascii=False)
                if draft.kind == "dictation":
                    assert draft.key["audio_text"] not in prompt
                else:
                    assert "audio_text" not in prompt and set(draft.prompt) == {"kind", "options"}
            shadow = audio.shadow(stage, word)
            if shadow is not None:
                assert shadow.prompt["sentence"] == shadow.key["audio_text"] and shadow.skill == "speaking"
    first = audio.dictation(pool_for("pre-a1"), pool_for("pre-a1").words[0], single=True)
    assert first.key["accepted"] == [pool_for("pre-a1").words[0].term], "at pre-A1 the word alone"


def test_speech_is_planned_only_with_allowance_and_never_in_a_tapped_session():
    stage = pool_for("a1")
    met = frozenset(word.key for word in stage.words[:200])
    kinds = set()
    for seed in range(40):
        kinds |= {d.kind for d in blueprints.plan(stage, random.Random(seed), size=10, met=met, audio=True)}
        assert not SPEECH & {d.kind for d in blueprints.plan(stage, random.Random(seed), size=10, met=met)}
        tapped = {d.kind for d in blueprints.plan(stage, random.Random(seed), size=5, met=met, audio=True, typing=False)}
        assert not tapped & {"dictation", "shadow", "typed_recall", "cloze_typed"}
    assert SPEECH <= kinds


def _with_stt(text: str):
    from dlp.main import app

    app.dependency_overrides[providers_dep] = lambda: replace(get_providers(), stt=FixtureSpeechToText(default_text=text))
    return app


def _session_with(client, kind, tag=""):
    """The first of a few seeded sessions with an item of `kind`; the learner knows some words, so the kinds
    beyond recognition come up."""
    for word in pool_for("a1").words[:12]:
        client.post("/words", headers=auth_headers(), json={"term": word.term, "meaning_en": word.meaning["en"]})
    for n in range(40):
        view = client.post("/exercises/sessions", headers=auth_headers(),
                           json={"request_id": f"speech-{kind[:8]}{tag}-{n:04d}", "stage_id": "a1", "size": 12,
                                 "fresh": True}).json()
        item = next((entry for entry in view["items"] if entry["kind"] == kind), None)
        if item:
            return view, item
    raise AssertionError(f"no {kind} item in 40 sessions")


def _url(view, item, action):
    return f"/exercises/sessions/{view['id']}/items/{item['id']}/{action}"


def _key(item):
    with session_scope() as session:
        return session.scalar(select(ExerciseItem.key).where(ExerciseItem.id == uuid.UUID(item["id"])))


def test_the_sound_of_an_item_comes_from_the_cache(client):
    view, item = _session_with(client, "listen_choose")
    first = client.post(_url(view, item, "audio"), headers=auth_headers("speech-audio-0001"))
    assert first.status_code == 200 and first.headers["content-type"] == "audio/wav"
    used = client.get("/usage", headers=auth_headers("speech-usage-01")).json()["counters"]["audio_seconds"]
    again = client.post(_url(view, item, "audio"), headers=auth_headers("speech-audio-0002"))
    assert again.headers["x-audio-cached"] == "1" and again.content == first.content
    after = client.get("/usage", headers=auth_headers("speech-usage-02")).json()["counters"]["audio_seconds"]
    assert after["daily"]["used"] == used["daily"]["used"], "a cached sound costs nothing"
    choice = next(entry for entry in view["items"] if entry["kind"] == "choice")
    assert client.post(_url(view, choice, "audio"), headers=auth_headers("speech-audio-0003")).status_code == 422
    skipped = client.post(_url(view, item, "skip"), headers=auth_headers(),
                          json={"request_id": "speech-skip-0001", "reason": "no_audio"}).json()
    assert skipped["closed"] and skipped["points"] == 0
    finished = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                           json={"request_id": "speech-finish-01", "early": True}).json()
    assert all(missed["ref"] != item_ref for missed in finished["summary"]["missed"]
               for item_ref in [_key(item)["refs"][_key(item)["answer"]]]), "a sound that did not play is no miss"


def test_a_short_allowance_plans_no_speech(client, settings, monkeypatch):
    monkeypatch.setattr(settings, "usage_daily_audio_seconds", 30)
    for n in range(10):
        view = client.post("/exercises/sessions", headers=auth_headers(),
                           json={"request_id": f"speech-short-{n:04d}", "stage_id": "a1", "size": 12,
                                 "fresh": True}).json()
        assert not SPEECH & {entry["kind"] for entry in view["items"]}


def test_shadowing_is_heard_or_not_heard_and_never_a_mistake(client):
    view, item = _session_with(client, "shadow")
    sentence = item["prompt"]["sentence"]
    assert client.post(_url(view, item, "answer"), headers=auth_headers(),
                       json={"request_id": "speech-shadow-000", "answer": {"text": sentence}}).status_code == 422
    app = _with_stt(sentence)
    try:
        heard = client.post(_url(view, item, "recording"), headers=auth_headers(),
                            data={"request_id": "speech-shadow-001"},
                            files={"audio": ("take.wav", tone_wav(1.0), "audio/wav")})
        again = client.post(_url(view, item, "recording"), headers=auth_headers(),
                            data={"request_id": "speech-shadow-001"},
                            files={"audio": ("take.wav", tone_wav(1.0), "audio/wav")})
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    body = heard.json()
    assert heard.status_code == 200, heard.text
    assert (body["outcome"], body["closed"], body["points"]) == ("heard", True, 1)
    assert "score" not in json.dumps(body) and body["feedback"]["matched_words"] > 0
    assert again.json() == body, "a retried recording replays what it got"
    other, quiet = _session_with(client, "shadow", tag="b")
    app = _with_stt("")
    try:
        silent = client.post(_url(other, quiet, "recording"), headers=auth_headers(),
                             data={"request_id": "speech-shadow-002"},
                             files={"audio": ("take.wav", tone_wav(1.0), "audio/wav")}).json()
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    assert (silent["outcome"], silent["closed"], silent["points"]) == ("not_heard", True, 0)
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(LearnerMistake)) == 0


def test_a_dictation_is_typed_and_judged_tolerantly(client):
    view, item = _session_with(client, "dictation")
    assert set(item["prompt"]) == {"kind", "word_count"}
    sentence = _key(item)["accepted"][0]
    reply = client.post(_url(view, item, "answer"), headers=auth_headers(),
                        json={"request_id": "speech-dict-0001", "answer": {"text": sentence.lower().rstrip(".")}}).json()
    assert reply["outcome"] == "correct" and reply["closed"] and reply["points"] == 1
