"""Video lessons: the script is validated like an episode, the render is budgeted per second, the file plays
with byte ranges, the subtitles come from the rendered file, and failures give the seconds back."""
from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from dlp.config import get_settings
from dlp.db.session import session_scope
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.service import drain
from dlp.domains.stories import service as stories
from dlp.domains.usage.models import UsageCounter, UsageReservation
from dlp.domains.videos import media, service
from dlp.domains.videos.models import VideoLesson
from dlp.domains.videos.schemas import VideoScript
from dlp.providers.base import ProviderError, VideoJobStatus, VideoRenderer, VideoRequest, VideoScene
from dlp.providers.registry import get_providers
from dlp.providers.video_azure import AzureAvatarRenderer, endpoint_for, parse_status, script_ssml
from dlp.providers.video_local import SceneCardRenderer, split_sentences, srt_for

from .conftest import FIXTURES, auth_headers

GOOD = json.loads((FIXTURES / "chat_replies.json").read_text(encoding="utf-8"))["video-script-v1"]["default"]


@pytest.fixture(autouse=True)
def video_allowance(monkeypatch):
    monkeypatch.setattr(get_settings(), "usage_daily_tokens", 40_000)
    monkeypatch.setattr(get_settings(), "usage_total_tokens", 400_000)


def allowed_a1() -> frozenset[str]:
    return frozenset(w for key in stories.stage_vocabulary("a1") for w in key.split())


def script(**changes) -> VideoScript:
    data = deepcopy(GOOD)
    data.update(changes)
    return VideoScript.model_validate(data)


def _request(client, request_id="video-req-0001", **body):
    payload = {"request_id": request_id, "stage_id": "a1", "topic": "op de markt", "kind": "uitleg", **body}
    return client.post("/videos", headers=auth_headers(request_id), json=payload)


# --- profile and script checks -------------------------------------------------------------------------------

def test_the_video_profile_keeps_every_level_within_a_short_video():
    a1 = service.video_profile("a1", 150)
    assert (a1.min_words, a1.max_words, a1.min_paragraphs, a1.max_paragraphs) == (60, 130, 3, 6)
    c2 = service.video_profile("c2", 150)
    assert c2.max_words <= 150 * service.WORDS_PER_SECOND and c2.min_words < c2.max_words
    assert service.estimate_seconds(130, 4) < 150 < service.estimate_seconds(400, 6)
    # Every level's shortest script still speaks for at least twenty seconds.
    for stage in ("pre-a1", "a1", "b2", "c2"):
        profile = service.video_profile(stage, 150, 20)
        assert service.estimate_seconds(profile.min_words, profile.min_paragraphs) >= 20, stage
    short = service.video_profile("pre-a1", 150, 45)
    assert service.estimate_seconds(short.min_words, 3) >= 45 and short.min_words < short.max_words


def test_a_script_that_speaks_for_less_than_twenty_seconds_is_sent_back():
    tiny = script(paragraphs=["Goeiemorgen! Vandaag gaan we naar de markt.", "Ik koop appels.", "Tot morgen!"],
                  paragraphs_en=["a", "b", "c"], paragraphs_fa=["a", "b", "c"], keywords=["markt", "appels", "morgen"],
                  questions=[{"prompt": "Wat koop ik?", "options": ["Appels.", "Brood.", "Kaas."], "answer_index": 0,
                              "evidence": "Ik koop appels."}] * 2)
    result = service.check_script(tiny, service.video_profile("a1", 150), allowed_a1())
    assert not result.ok
    too_short = next(item for item in result.hard if item.startswith("video_too_short"))
    assert "minstens 20" in too_short and "Schrijf minstens" in too_short
    assert result.metrics["estimated_seconds"] < 20
    assert service.check_script(script(), service.video_profile("a1", 150), allowed_a1()).metrics["estimated_seconds"] >= 20


def test_the_fixture_script_passes_the_a1_gate_and_a_missing_keyword_fails_it():
    result = service.check_script(script(), service.video_profile("a1", 150), allowed_a1())
    assert result.ok, result.hard
    broken = service.check_script(script(keywords=GOOD["keywords"][:3]), service.video_profile("a1", 150), allowed_a1())
    assert not broken.ok and any(item.startswith("scene_count_mismatch") for item in broken.hard)


def test_the_schema_refuses_blank_scenes_and_too_few_scenes():
    with pytest.raises(ValueError):
        script(paragraphs=["Goeiemorgen.", "  ", "Tot morgen."], paragraphs_en=["a", "b", "c"], paragraphs_fa=["a", "b", "c"],
               keywords=["a", "b", "c"])
    with pytest.raises(ValueError):
        script(paragraphs=GOOD["paragraphs"][:2])


# --- the whole path with the fixture renderer ---------------------------------------------------------------

def test_a_requested_video_is_written_rendered_subtitled_and_playable(client):
    response = _request(client)
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["status"] == "queued" and created["kind_label"] == "Uitleg" and created["stage_id"] == "a1"
    assert _request(client).json()["id"] == created["id"], "the same request id returns the same lesson"

    assert drain(get_settings()) == 2, "the script job and one render poll"
    detail = client.get(f"/videos/{created['id']}", headers=auth_headers()).json()
    assert detail["status"] == "ready", detail
    assert detail["title"] == "Op de markt" and detail["presenter"] == "scene-cards" and detail["renderer"] == "fixture"
    assert len(detail["scenes"]) == 4 and detail["scenes"][0]["keyword"] == "de markt" and detail["scenes"][0]["fa"]
    assert detail["duration_seconds"] > 5 and detail["cues"], "subtitles came out of the rendered file"
    assert all(set(cue) >= {"start", "end", "text", "scene"} for cue in detail["cues"])
    assert [cue["scene"] for cue in detail["cues"]] == sorted(cue["scene"] for cue in detail["cues"])
    assert detail["cues"][0]["text"] == "Goeiemorgen!" and detail["cues"][-1]["scene"] == 3
    assert detail["word_count"] == 72 and detail["provider"] == "fixture" and detail["answered"] is False

    subtitles = client.get(f"/videos/{created['id']}/subtitles.vtt", headers=auth_headers())
    assert subtitles.status_code == 200 and subtitles.headers["content-type"].startswith("text/vtt")
    assert subtitles.text.startswith("WEBVTT") and "Goeiemorgen!" in subtitles.text

    whole = client.get(f"/videos/{created['id']}/media", headers=auth_headers())
    assert whole.status_code == 200 and whole.headers["content-type"] == "video/mp4"
    assert whole.headers["accept-ranges"] == "bytes" and int(whole.headers["content-length"]) == len(whole.content)
    assert whole.content[4:8] == b"ftyp" and b"moov" in whole.content[:4096], "progressive playback: index first"
    part = client.get(f"/videos/{created['id']}/media", headers={**auth_headers(), "Range": "bytes=100-199"})
    assert part.status_code == 206 and len(part.content) == 100 and part.content == whole.content[100:200]
    assert part.headers["content-range"] == f"bytes 100-199/{len(whole.content)}"
    tail = client.get(f"/videos/{created['id']}/media", headers={**auth_headers(), "Range": "bytes=-50"})
    assert tail.status_code == 206 and tail.content == whole.content[-50:]
    beyond = client.get(f"/videos/{created['id']}/media", headers={**auth_headers(), "Range": f"bytes={len(whole.content) + 5}-"})
    assert beyond.status_code == 416

    usage = client.get("/usage", headers=auth_headers()).json()["counters"]["video_seconds"]["daily"]
    assert usage["reserved"] == 0 and 5 < usage["used"] == pytest.approx(detail["duration_seconds"], abs=0.01)

    plan = client.get("/today", headers=auth_headers()).json()
    assert plan["videos"]["ready"]["id"] == created["id"] and plan["videos"]["pending"] == 0


def test_watching_answering_and_saving_words_award_points_once(client):
    created = _request(client, "video-req-0002").json()
    drain(get_settings())
    video_id = created["id"]
    watched = client.post(f"/videos/{video_id}/watched", headers=auth_headers("watch-0001")).json()
    assert watched["watched_at"]
    client.post(f"/videos/{video_id}/watched", headers=auth_headers("watch-0002"))
    answered = client.post(f"/videos/{video_id}/answers", headers=auth_headers("answer-0001"),
                           json={"request_id": "answer-0001", "answers": {"0": 1, "1": 0}}).json()
    assert answered["answered"] and [q["correct"] for q in answered["questions"]] == [True, False]
    assert answered["questions"][1]["evidence"] == "Dat is drie euro."
    again = client.post(f"/videos/{video_id}/answers", headers=auth_headers("answer-0002"),
                        json={"request_id": "answer-0002", "answers": {"0": 0, "1": 0}})
    assert again.status_code == 409
    saved = client.post(f"/videos/{video_id}/words", headers=auth_headers("word-0001"), json={"term": "de verkoper"}).json()
    assert saved["created"] and saved["item"]["source_kind"] == "video" and saved["item"]["meaning_fa"] == "فروشنده"
    missing = client.post(f"/videos/{video_id}/words", headers=auth_headers("word-0002"), json={"term": "fiets"})
    assert missing.status_code == 404
    rated = client.post(f"/videos/{video_id}/rating", headers=auth_headers("rate-0001"), json={"rating": 1}).json()
    assert rated["rating"] == 1
    plan = client.get("/today", headers=auth_headers()).json()
    assert plan["goal"]["points"] == service.POINTS["watch"] + service.POINTS["answer"]
    with session_scope() as session:
        from dlp.domains.stories.models import LearningDay
        day = session.scalar(select(LearningDay))
        assert day is not None and day.videos_watched == 1 and day.questions_correct == 1


def test_two_pending_videos_are_the_limit_and_the_library_lists_them(client):
    assert _request(client, "pending-0001").status_code == 201
    assert _request(client, "pending-0002", topic="").status_code == 201
    refused = _request(client, "pending-0003")
    assert refused.status_code == 409
    listing = client.get("/videos", headers=auth_headers()).json()
    assert len(listing["items"]) == 2 and listing["max_pending"] == 2 and listing["renderer"]["name"] == "fixture"
    assert {item["status"] for item in listing["items"]} == {"queued"}
    assert all(item["topic"] for item in listing["items"]), "an empty wish gets a topic from the stage bank"
    assert [level["id"] for level in listing["levels"]][:2] == ["pre-a1", "a1"]
    bad = client.post("/videos", headers=auth_headers("bad-stage-01"),
                      json={"request_id": "bad-stage-01", "stage_id": "z9", "topic": "", "kind": "uitleg"})
    assert bad.status_code == 404


# --- failure paths -------------------------------------------------------------------------------------------

class FailingRenderer(VideoRenderer):
    name = "fixture-failing"
    label = "scene-cards"

    def __init__(self, *, at: str) -> None:
        self.at = at
        self.cleaned: list[str] = []

    def start(self, request: VideoRequest, *, request_id: str = "") -> str:
        if self.at == "start":
            raise ProviderError("the renderer refused the job")
        return "job-1"

    def status(self, job_id: str) -> VideoJobStatus:
        if self.at == "status":
            return VideoJobStatus("failed", detail="synthesis error 4711")
        return VideoJobStatus("running")

    def fetch(self, job_id: str, destination: Path) -> None:
        raise ProviderError("nothing to fetch")

    def cleanup(self, job_id: str) -> None:
        self.cleaned.append(job_id)


def _counter(metric: str = "video_seconds") -> tuple[float, float]:
    with session_scope() as session:
        row = session.scalar(select(UsageCounter).where(UsageCounter.metric == metric, UsageCounter.scope == "daily"))
        return (float(row.used), float(row.reserved)) if row else (0.0, 0.0)


def test_a_render_that_fails_gives_the_seconds_back_and_keeps_the_script(client, monkeypatch):
    renderer = FailingRenderer(at="status")
    monkeypatch.setattr(get_providers(), "video", renderer)
    created = _request(client, "fail-0001").json()
    drain(get_settings())
    detail = client.get(f"/videos/{created['id']}", headers=auth_headers()).json()
    assert detail["status"] == "failed" and detail["error_code"] == "render"
    assert detail["failure_reasons"] == ["synthesis error 4711"] and renderer.cleaned == ["job-1"]
    assert _counter() == (0.0, 0.0), "the reserved seconds were released"
    with session_scope() as session:
        lesson = session.get(VideoLesson, uuid.UUID(created["id"]))
        assert lesson is not None and lesson.scenes and lesson.title == "Op de markt", "the script survives a render failure"
        assert "video_reservation" not in lesson.checks
        reservations = list(session.scalars(select(UsageReservation).where(UsageReservation.metric == "video_seconds")))
        assert [r.state for r in reservations] == ["released"]

    # A retry re-renders without paying the writer again.
    monkeypatch.setattr(get_providers(), "video", SceneCardRenderer(get_providers().tts, work_dir=Path("/tmp/dlp-video-test"),
                                                                     name="fixture", fast=True))
    calls_before = _counter("model_calls")[0]
    retried = client.post(f"/videos/{created['id']}/retry", headers=auth_headers("retry-0001")).json()
    assert retried["status"] == "queued"
    drain(get_settings())
    detail = client.get(f"/videos/{created['id']}", headers=auth_headers()).json()
    assert detail["status"] == "ready" and detail["cues"]
    assert _counter("model_calls")[0] == calls_before, "no second writer call"


def test_a_renderer_that_refuses_the_job_fails_the_lesson_without_a_reservation(client, monkeypatch):
    monkeypatch.setattr(get_providers(), "video", FailingRenderer(at="start"))
    created = _request(client, "fail-0002").json()
    assert drain(get_settings()) == 1
    detail = client.get(f"/videos/{created['id']}", headers=auth_headers()).json()
    assert detail["status"] == "failed" and detail["error_code"] == "render"
    assert detail["failure_reasons"] == ["the renderer refused the job"]
    assert _counter() == (0.0, 0.0)


def test_a_render_that_never_finishes_times_out(client, monkeypatch):
    monkeypatch.setattr(get_providers(), "video", FailingRenderer(at="never"))
    monkeypatch.setattr(service, "MAX_RENDER_POLLS", 2)
    created = _request(client, "fail-0003").json()
    drain(get_settings())
    with session_scope() as session:
        lesson = session.get(VideoLesson, uuid.UUID(created["id"]))
        assert lesson is not None and lesson.status == "failed" and lesson.error_code == "render_timeout"
        polls = list(session.scalars(select(Job).where(Job.kind == "video_render")))
        assert len(polls) == 3 and all(job.status == "done" for job in polls)
    assert _counter() == (0.0, 0.0)


def test_the_video_allowance_refuses_a_render_before_it_starts(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "usage_daily_video_seconds", 10)
    created = _request(client, "allowance-0001").json()
    drain(get_settings())
    detail = client.get(f"/videos/{created['id']}", headers=auth_headers()).json()
    assert detail["status"] == "failed" and detail["error_code"] == "allowance_video"
    assert _counter() == (0.0, 0.0)


# --- renderers ----------------------------------------------------------------------------------------------

def test_scene_cards_split_sentences_and_time_subtitles_by_length():
    assert split_sentences("Goeiemorgen! Ik ben Lisa. Tot morgen…") == ["Goeiemorgen!", "Ik ben Lisa.", "Tot morgen…"]
    srt = srt_for([("Eerste zin. Tweede zin is langer.", 0.0, 4.0), ("Derde.", 4.6, 1.0)])
    cues = media.parse_srt(srt)
    assert [cue["text"] for cue in cues] == ["Eerste zin.", "Tweede zin is langer.", "Derde."]
    assert cues[0]["end"] == cues[1]["start"] and cues[1]["end"] == pytest.approx(4.0, abs=0.01)
    assert cues[2]["start"] == pytest.approx(4.6, abs=0.01)


def test_cues_are_attached_to_their_scene_by_text_then_by_overlap():
    cues = [{"start": 0, "end": 1, "text": "Goeiemorgen!"}, {"start": 1, "end": 2, "text": "De markt is op zaterdag."},
            {"start": 2, "end": 3, "text": "Ik betaal en zeg dank u"}, {"start": 3, "end": 4, "text": "<i>Tot morgen!</i>"}]
    scenes = ["Goeiemorgen! De markt is op zaterdag.", "Ik betaal en zeg dank u.", "Tot morgen! Probeer het zelf."]
    assert [cue["scene"] for cue in media.assign_scenes(cues, scenes)] == [0, 0, 1, 2]
    assert media.vtt_for(media.assign_scenes(cues, scenes)).count("-->") == 4


def test_the_azure_avatar_renderer_submits_polls_downloads_and_cleans_up():
    seen: list[httpx.Request] = []
    state = {"polls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "files.example.net":
            assert "Authorization" not in request.headers and "Ocp-Apim-Subscription-Key" not in request.headers
            return httpx.Response(200, content=b"\x00" * 2048)
        assert request.headers["Authorization"] == "Bearer token-123"
        assert request.url.params["api-version"] == "2024-08-01"
        if request.method == "PUT":
            body = json.loads(request.content)
            assert body["inputKind"] == "SSML" and body["avatarConfig"]["videoCodec"] == "h264"
            assert body["avatarConfig"]["subtitleType"] == "soft_embedded"
            assert body["avatarConfig"]["talkingAvatarCharacter"] == "lisa"
            ssml = body["inputs"][0]["content"]
            assert "nl-BE-DenaNeural" in ssml and "De markt &amp; ik" in ssml and ssml.count("<break") == 3
            return httpx.Response(201, json={"id": request.url.path.rsplit("/", 1)[-1], "status": "NotStarted"})
        if request.method == "GET":
            state["polls"] += 1
            if state["polls"] == 1:
                return httpx.Response(200, json={"status": "Running"})
            return httpx.Response(200, json={"status": "Succeeded", "properties": {"durationInMilliseconds": 41500},
                                             "outputs": {"result": "https://files.example.net/video.mp4?sig=abc"}})
        if request.method == "DELETE":
            return httpx.Response(204)
        raise AssertionError(request.method)

    renderer = AzureAvatarRenderer(endpoint="https://dlp-speech-x.cognitiveservices.azure.com", voice="nl-BE-DenaNeural",
                                   token_provider=lambda: "token-123", transport=httpx.MockTransport(handler))
    request = VideoRequest(scenes=[VideoScene("Goeiemorgen.", "markt"), VideoScene("De markt & ik.", "ik")], title="Markt")
    job = renderer.start(request)
    assert job.startswith("dlp-") and len(job) <= 64
    assert renderer.status(job).state == "running"
    done = renderer.status(job)
    assert done.state == "succeeded" and done.duration_ms == 41500
    target = Path("/tmp/dlp-avatar-test.mp4")
    renderer.fetch(job, target)
    assert target.stat().st_size == 2048
    renderer.cleanup(job)
    assert [r.method for r in seen] == ["PUT", "GET", "GET", "GET", "GET", "DELETE"]


def test_azure_avatar_status_and_endpoint_helpers():
    assert parse_status({"status": "Failed", "properties": {"error": {"message": "bad voice"}}}).detail == "bad voice"
    assert parse_status({"status": "NotStarted"}).state == "pending"
    resource = "/subscriptions/s/resourceGroups/g/providers/Microsoft.CognitiveServices/accounts/dlp-speech-abc"
    assert endpoint_for(resource_id=resource) == "https://dlp-speech-abc.cognitiveservices.azure.com"
    assert endpoint_for(region="westeurope") == "https://westeurope.api.cognitive.microsoft.com"
    assert endpoint_for(endpoint="https://custom.example.com/") == "https://custom.example.com"
    renderer = AzureAvatarRenderer(endpoint="", voice="nl-BE-DenaNeural")
    assert renderer.available()[0] is False
    ssml = script_ssml(VideoRequest(scenes=[VideoScene("<b>Dag</b>", "dag")], title="t"), "nl-BE-ArnaudNeural")
    assert "&lt;b&gt;Dag&lt;/b&gt;" in ssml and 'xml:lang="nl-BE"' in ssml


def test_a_refused_credential_is_reported_as_unavailable():
    renderer = AzureAvatarRenderer(endpoint="https://x.cognitiveservices.azure.com", voice="v", key="k",
                                   transport=httpx.MockTransport(lambda request: httpx.Response(401)))
    with pytest.raises(ProviderError, match="refused the credentials"):
        renderer.start(VideoRequest(scenes=[VideoScene("Dag.", "dag")], title="t"))
