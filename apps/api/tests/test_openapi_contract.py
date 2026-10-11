"""The HTTP contract: the OpenAPI schema must build without the docs being served, and the set of operations
without a response model may only shrink.

Every route written before October 2026 returns a hand-built dict. New routes declare a Pydantic response
model (so the schema describes them and the web types can be generated); when a legacy route is typed,
remove it from LEGACY_UNTYPED in the same change.
"""

from __future__ import annotations

from dlp.main import app

LEGACY_UNTYPED = frozenset(
    {
        "DELETE /words/{item_id}",
        "GET /coach/history",
        "GET /coach/plan",
        "GET /content-review/{stage_id}",
        "GET /curriculum",
        "GET /curriculum/attempts/{attempt_id}",
        "GET /curriculum/{stage_id}",
        "GET /curriculum/{stage_id}/topics",
        "GET /curriculum/{stage_id}/topics/{topic_id}",
        "GET /export",
        "GET /health/ready",
        "GET /library/{stage_id}",
        "GET /library/{stage_id}/stories",
        "GET /library/{stage_id}/stories/{story_id}",
        "GET /library/{stage_id}/vocabulary",
        "GET /missions/{mission_id}/audio/{audio_key}",
        "GET /practice/sessions/{session_id}/turns/{turn_id}/audio",
        "GET /stories",
        "GET /stories/episodes/{episode_id}",
            "GET /topic-conversations",
        "GET /topic-conversations/blueprints/{blueprint_id}",
        "GET /topic-conversations/{conversation_id}",
        "GET /videos",
        "GET /videos/{video_id}",
        "GET /videos/{video_id}/media",
        "GET /videos/{video_id}/subtitles.vtt",
        "GET /words",
        "POST /coach/plan",
        "POST /content-review/{stage_id}",
        "POST /curriculum/attempts/{attempt_id}/listening",
        "POST /curriculum/attempts/{attempt_id}/submit",
        "POST /curriculum/{stage_id}/listening",
        "POST /curriculum/{stage_id}/practice",
        "POST /curriculum/{stage_id}/test",
        "POST /curriculum/{stage_id}/topics/{topic_id}/listening",
        "POST /curriculum/{stage_id}/topics/{topic_id}/practice",
        "POST /curriculum/{stage_id}/writing-feedback",
        "POST /practice/sessions",
        "POST /speech/synthesize",
        "POST /stories/episodes",
        "POST /stories/episodes/{episode_id}/answers",
        "POST /stories/episodes/{episode_id}/choice",
        "POST /stories/episodes/{episode_id}/rating",
        "POST /stories/episodes/{episode_id}/read",
        "POST /stories/episodes/{episode_id}/read-aloud",
        "POST /stories/episodes/{episode_id}/retry",
        "POST /stories/episodes/{episode_id}/translate",
        "POST /stories/episodes/{episode_id}/words",
        "POST /stories/level",
        "POST /topic-conversations/start",
        "POST /topic-conversations/{conversation_id}/end",
        "POST /topic-conversations/{conversation_id}/turns",
        "POST /videos",
        "POST /videos/{video_id}/answers",
        "POST /videos/{video_id}/rating",
        "POST /videos/{video_id}/retry",
        "POST /videos/{video_id}/watched",
        "POST /videos/{video_id}/words",
        "POST /words",
        "POST /words/{item_id}/review",
    }
)


def _operations(schema: dict) -> dict[str, dict]:
    return {
        f"{method.upper()} {path}": operation
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
    }


def _is_untyped(operation: dict) -> bool:
    content = operation.get("responses", {}).get("200", {}).get("content", {})
    if any(media.startswith("audio/") for media in content):
        return False  # a sound declares its media type; there is no JSON body to model
    return not content.get("application/json", {}).get("schema")


def test_schema_builds_when_docs_are_not_served():
    schema = app.openapi()  # the test settings serve no /openapi.json; the schema is still generated
    assert len(schema["paths"]) >= 70


def test_untyped_operations_only_shrink():
    untyped = {name for name, operation in _operations(app.openapi()).items() if _is_untyped(operation)}
    new = sorted(untyped - LEGACY_UNTYPED)
    assert not new, f"new operations without a response model (declare one): {new}"
    typed_now = sorted(LEGACY_UNTYPED - untyped)
    assert not typed_now, f"these operations are typed now; remove them from LEGACY_UNTYPED: {typed_now}"
