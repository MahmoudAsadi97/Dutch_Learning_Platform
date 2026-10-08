"""The owner export covers every learner-scoped table, or says why a table is left out.

Walks the ORM metadata, so a table added later (activity events, exercise sessions, agent runs, ...)
cannot be forgotten silently: it must be exported or added to EXCLUDED with a reason.
"""

from __future__ import annotations

from dlp.db.registry import Base

# table -> top-level key of GET /export that carries its rows
EXPORTED = {
    "learners": "learner",
    "learner_profiles": "profile",
    "skill_records": "skill_records",
    "practice_sessions": "sessions",  # turns and evidence hang off the session rows
    "feedback_reports": "sessions",
    "practice_observations": "curriculum",
    "curriculum_practice": "curriculum",
    "topic_practice": "curriculum",
    "curriculum_attempts": "curriculum",
    "topic_conversations": "topic_conversations",
    "coach_plan_requests": "practice_plans",
    "content_reviews": "requested_content_reviews",
    "story_series": "stories",
    "story_episodes": "stories",
    "vocab_items": "words",
    "learning_days": "learning_days",
    "video_lessons": "videos",
    "usage_counters": "usage",
    "usage_reservations": "usage",
}

EXCLUDED = {
    "audio_assets": "binary recordings and syntheses; the transcripts travel with the turns and attempts",
}


def _learner_scoped_tables() -> set[str]:
    scoped = set()
    for table in Base.metadata.sorted_tables:
        if table.name == "learners" or any(column.name in ("learner_id", "requester_id") for column in table.columns):
            scoped.add(table.name)
    return scoped


def test_every_learner_scoped_table_is_exported_or_explicitly_excluded():
    scoped = _learner_scoped_tables()
    unaccounted = sorted(scoped - set(EXPORTED) - set(EXCLUDED))
    assert not unaccounted, f"add these tables to the export (or to EXCLUDED with a reason): {unaccounted}"
    stale = sorted((set(EXPORTED) | set(EXCLUDED)) - scoped)
    assert not stale, f"not learner-scoped tables (or gone): {stale}"


def test_export_payload_has_every_declared_key(client, headers):
    payload = client.get("/export", headers=headers).json()
    missing = sorted(set(EXPORTED.values()) - set(payload))
    assert not missing, f"export keys declared in EXPORTED but absent from the payload: {missing}"
    assert "episodes" in payload["stories"]
    assert isinstance(payload["words"], list) and isinstance(payload["learning_days"], list)
    assert isinstance(payload["videos"], list)
