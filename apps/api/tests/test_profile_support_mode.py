"""Retired support preferences remain readable while the interface offers Dutch and English."""
import pytest
from pydantic import ValidationError

from dlp.domains.profile.schemas import OnboardingBody, ProfileUpdate, ProfileView


@pytest.mark.parametrize("choice", ["nl", "nl-en"])
def test_profile_and_welcome_accept_current_modes(choice):
    assert ProfileUpdate(support_mode=choice).support_mode == choice
    assert OnboardingBody(support_mode=choice, stage_id="a1").support_mode == choice


@pytest.mark.parametrize("legacy", ["nl-fa", "nl-fa-en"])
def test_retired_preferences_are_read_as_english_without_mutating_the_source(legacy):
    stored = {
        "stage_id": "a1", "daily_goal_points": 20, "support_mode": legacy,
        "gloss_mode": "auto", "stated_goal": "", "onboarded_at": None,
        "earned_stage_id": None, "suggested_stage_id": None,
    }
    assert ProfileView.model_validate(stored).support_mode == "nl-en"
    assert stored["support_mode"] == legacy
    assert ProfileUpdate(support_mode=legacy).support_mode == "nl-en"


def test_unknown_preferences_remain_invalid_and_null_can_clear_the_preference():
    assert ProfileUpdate(support_mode=None).support_mode is None
    with pytest.raises(ValidationError):
        ProfileUpdate(support_mode="de")
