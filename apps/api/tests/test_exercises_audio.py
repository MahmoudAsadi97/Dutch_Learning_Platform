"""Exercises with speech (roadmap 3.5): a cached synthesis costs no allowance, prompts never carry the spoken
text, and shadowing is heard or not heard, never a score or a mistake."""
from __future__ import annotations

import json
import random
import uuid
from dataclasses import replace
from types import SimpleNamespace

from sqlalchemy import func, select, update

from dlp.api.deps import providers_dep
from dlp.db.session import session_scope
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises import audio, blueprints, service
from dlp.domains.exercises.compare import fold
from dlp.domains.exercises.graders import grade
from dlp.domains.exercises.models import ExerciseItem, ExerciseSession, LearnerMistake
from dlp.domains.exercises.pool import pool_for
from dlp.domains.identity.models import Learner
from dlp.domains.speech.service import TTS_CACHE_PREFIX, synthesize_cached, tts_cache_key
from dlp.domains.usage.service import snapshot
from dlp.providers.fixtures import FixtureSpeechToText, FixtureTextToSpeech, MemoryBlobStore, tone_wav
from dlp.providers.registry import get_providers
from tests.conftest import auth_headers

SPEECH = {"listen_choose", "dictation", "shadow"}
# stage -> (words with a sentence to dictate (3 to 12 words, no name), words with a sentence to shadow (3 to
# 10)); at pre-A1 the word alone is dictated. B1's examples are nearly all longer (roadmap 7.9 adds sentences).
# Measured 10 Oct 2026 on the content of 6 Oct.
SPOKEN = {
    "pre-a1": (466, 442), "a1": (430, 316), "pre-a2": (196, 59), "a2": (489, 500), "pre-b1": (367, 167),
    "b1": (30, 0), "pre-b2": (398, 392), "b2": (400, 393), "pre-c1": (399, 392), "c1": (275, 99),
    "pre-c2": (251, 87), "c2": (262, 86),
}
NAMES = {"Nora", "Noor", "Mina", "Yara", "Jonas", "Leyla", "Rob", "Emma", "Pieter", "Els", "Nadia"}


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


def test_which_stage_has_which_sentence_to_hear():
    assert list(SPOKEN) == list(STAGE_IDS)
    for stage_id, row in SPOKEN.items():
        available = pool_for(stage_id).available()
        assert (available["dictation"], available["shadow"]) == row, f"{stage_id}: content changed; re-measure"


def test_a_dictated_sentence_stands_nowhere_else_in_the_session():
    """Not on the intro card, not on another item's word cards or boards: one A1 example serves several words."""
    for stage_id in STAGE_IDS[1:]:
        stage = pool_for(stage_id)
        for seed in range(60):
            rng = random.Random(seed)
            met = frozenset(w.key for w in rng.sample(stage.words, rng.randrange(0, 300)))
            drafts = blueprints.plan(stage, rng, size=rng.randrange(5, 13), met=met, audio=True)
            for draft in drafts:
                if draft.kind == "dictation":
                    text = fold(draft.key["audio_text"])
                    for other in drafts:
                        if other is not draft:
                            shown = fold(json.dumps([other.prompt, other.key], ensure_ascii=False))
                            assert text not in shown, (stage_id, seed, other.kind)


def test_a_dictation_counts_words_the_way_answers_are_compared():
    stage = pool_for("a2")
    word = next(stage.by_id[i] for i, text in stage.dictated.items() if "e-mail" in text)
    draft = audio.dictation(stage, word)
    assert draft.prompt["word_count"] == len(draft.key["audio_text"].split()), "'e-mail' is one word"


def _names(text: str) -> set[str]:
    return NAMES & set(text.strip(".!?").replace(",", " ").split())


def test_a_name_cannot_be_heard_so_none_is_dictated():
    for stage_id in STAGE_IDS:
        assert not any(_names(text) for text in pool_for(stage_id).dictated.values()), stage_id
    assert any(_names(text) for text in pool_for("b2").shadowed.values()), "shadowing shows its sentence"


def test_a_listened_noun_is_offered_among_nouns_of_its_article():
    stage = pool_for("a1")
    alone = total = 0
    for word in stage.words:
        draft = audio.listen_choose(stage, word, random.Random(word.id)) if word.article else None
        if draft is not None:
            articles = [stage.by_id[ref.removeprefix("word:")].article for ref in draft.key["refs"].values()]
            total += 1
            alone += articles.count(word.article) == 1
    assert total > 250 and alone <= total // 50, "hearing 'het' alone must not pick the answer"


def test_a_dictation_miss_elsewhere_in_the_sentence_is_not_the_words():
    key = {"accepted": ["Ik leg de identiteitskaart klaar voor mijn afspraak."], "article": "none",
           "word": {"term": "de identiteitskaart"}}
    item = SimpleNamespace(kind="dictation", key=key)
    prompt = {"kind": "dictation", "word_count": 8}
    for typed, blamed in (("ik leg de identiteitskaart klaar voor afspraak", False),
                          ("ik leg de kaart klaar voor mijn afspraak", True),
                          ("ik leg klaar voor mijn afspraak", True)):
        judged = grade("dictation", prompt, key, {"text": typed}, frozenset())
        assert judged.outcome == "incorrect", typed
        assert service._word_missed(item, judged.feedback) is blamed, typed
    assert service._word_missed(item, None), "a skipped dictation is a miss of the word"


def test_speech_is_planned_only_with_allowance_and_no_typed_or_spoken_kind_in_a_tapped_session():
    stage = pool_for("a2")  # at A1 one example serves several words, so a dictation is rarer
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


def _session_with(client, kind, tag="", stage="a1"):
    """The first of a few seeded sessions with an item of `kind`; the learner knows some words, so the kinds
    beyond recognition come up."""
    for word in pool_for(stage).words[:12]:
        client.post("/words", headers=auth_headers(), json={"term": word.term, "meaning_en": word.meaning["en"]})
    for n in range(40):
        view = client.post("/exercises/sessions", headers=auth_headers(),
                           json={"request_id": f"speech-{kind[:8]}{tag}-{n:04d}", "stage_id": stage, "size": 12,
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
    summary = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                          json={"request_id": "speech-finish-02", "early": True}).json()["summary"]
    assert summary["by_kind"]["shadow"]["first_try_correct"] == 1, "heard is right the first time"
    other, quiet = _session_with(client, "shadow", tag="b")
    app = _with_stt("")
    try:
        takes = [client.post(_url(other, quiet, "recording"), headers=auth_headers(),
                             data={"request_id": f"speech-shadow-00{n}"},
                             files={"audio": ("take.wav", tone_wav(1.0), "audio/wav")}).json() for n in (2, 3)]
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    first, second = takes
    assert (first["outcome"], first["closed"], first["attempts_left"], first["points"]) == ("not_heard", False, 1, 0)
    assert not first["requeue"] and first["progress"]["queued"] == 0, "tried again at once, not at the end"
    assert (second["outcome"], second["closed"], second["points"]) == ("not_heard", True, 0)
    with session_scope() as session:
        assert session.scalar(select(func.count()).select_from(LearnerMistake)) == 0


def test_a_dictation_is_typed_and_judged_tolerantly(client):
    view, item = _session_with(client, "dictation", stage="a2")
    assert set(item["prompt"]) == {"kind", "word_count"}
    sentence = _key(item)["accepted"][0]
    reply = client.post(_url(view, item, "answer"), headers=auth_headers(),
                        json={"request_id": "speech-dict-0001", "answer": {"text": sentence.lower().rstrip(".")}}).json()
    assert reply["outcome"] == "correct" and reply["closed"] and reply["points"] == 1


def test_a_recording_refused_after_its_transcription_keeps_its_usage(client, monkeypatch):
    """The session closed while the recording was transcribed: the refusal is returned, not raised, so the paid
    transcription stays counted."""
    view, item = _session_with(client, "shadow", tag="c")
    real = service.transcribe_upload

    def closing(session, *args, **kwargs):
        transcribed = real(session, *args, **kwargs)
        session.execute(update(ExerciseSession).where(ExerciseSession.id == uuid.UUID(view["id"]))
                        .values(status="abandoned"))
        return transcribed

    monkeypatch.setattr(service, "transcribe_upload", closing)
    before = client.get("/usage", headers=auth_headers("speech-usage-03")).json()["counters"]["audio_seconds"]
    app = _with_stt(item["prompt"]["sentence"])
    try:
        refused = client.post(_url(view, item, "recording"), headers=auth_headers(),
                              data={"request_id": "speech-shadow-003"},
                              files={"audio": ("take.wav", tone_wav(1.0), "audio/wav")})
    finally:
        app.dependency_overrides.pop(providers_dep, None)
    assert refused.status_code == 409 and refused.json()["code"] == "session_closed"
    after = client.get("/usage", headers=auth_headers("speech-usage-04")).json()["counters"]["audio_seconds"]
    assert after["daily"]["used"] > before["daily"]["used"], "the transcription stays paid for"


def test_a_skipped_shadowing_closes_and_is_no_missed_word(client):
    view, item = _session_with(client, "shadow", tag="d")
    skipped = client.post(_url(view, item, "skip"), headers=auth_headers(),
                          json={"request_id": "speech-skip-0002", "reason": "unknown"}).json()
    assert skipped["closed"] and not skipped["requeue"]
    summary = client.post(f"/exercises/sessions/{view['id']}/finish", headers=auth_headers(),
                          json={"request_id": "speech-finish-03", "early": True}).json()["summary"]
    assert summary["skipped"] == 1 and not any(missed["ref"] == _key(item)["refs"]["answer"]
                                               for missed in summary["missed"])


def test_a_lesson_listening_text_is_made_once_too(client):
    first = client.post("/curriculum/a1/listening", headers=auth_headers("listen-cache-01"))
    again = client.post("/curriculum/a1/listening", headers=auth_headers("listen-cache-02"))
    assert first.status_code == 200 and first.headers["x-audio-cached"] == "0"
    assert again.headers["x-audio-cached"] == "1" and again.content == first.content
