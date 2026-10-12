"""The reminder must not cancel the same appointment the learner needs to change."""

from dlp.domains.content.schemas import MissionDocument
from dlp.domains.content.service import CONTENT_DIR


def test_reminder_and_rescheduling_share_one_premise():
    mission = MissionDocument.model_validate_json(
        (CONTENT_DIR / "missions" / "appointment-change" / "mission.json").read_text()
    )
    listening = next(step.payload for step in mission.steps if step.key == "listen-voicemail")
    speaking = next(step.payload for step in mission.steps if step.key == "speak-call")
    assert mission.version >= 3
    assert "woensdag om twee uur" in listening.transcript.nl
    assert "ziek" not in listening.transcript.nl.lower()
    assert "ill" not in listening.transcript.en.lower()
    assert "بیمار" not in listening.transcript.fa
    assert listening.questions[0].options[listening.questions[0].answer_index].nl == (
        "Herinnering aan uw afspraak"
    )
    assert "state_reason" in speaking.required_actions
    assert "v3" in listening.audio_key
