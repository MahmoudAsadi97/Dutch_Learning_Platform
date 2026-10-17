"""The selected skill has matching goals, without exposing a receptive answer key."""
from __future__ import annotations

from copy import deepcopy

import pytest

from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS
from dlp.domains.curriculum.topics import skill_objectives, topics_for


@pytest.mark.parametrize("stage_id", STAGE_IDS)
@pytest.mark.parametrize("skill", SKILLS)
def test_every_stage_has_objectives_for_the_selected_skill(stage_id, skill):
    bank = topics_for(stage_id)
    for topic in bank.topics:
        before = topic.model_dump_json()
        goals = skill_objectives(topic, skill)
        assert goals
        assert all(set(goal) == {"nl", "en", "fa"} and all(goal.values()) for goal in goals)
        activity = getattr(topic, skill)
        if skill in ("reading", "listening"):
            assert goals[0]["nl"].startswith("Lees" if skill == "reading" else "Luister")
            assert goals[1:] == [question.prompt.model_dump() for question in activity.questions]
            # No options, answer positions or worked explanation belong in a learning goal.
            assert all(set(goal) == {"nl", "en", "fa"} for goal in goals)
        else:
            assert goals == [criterion.model_dump() for criterion in activity.criteria]
        assert topic.model_dump_json() == before


def test_cooking_listening_does_not_require_asking_the_cooking_partner():
    bank = topics_for("pre-a2")
    topic = next(topic for topic in bank.topics if "kookpartner" in topic.objectives[0].nl)
    goals = skill_objectives(topic, "listening")
    assert not any("kookpartner" in goal["nl"] for goal in goals)
    assert any("wortels" in goal["nl"] for goal in goals)
    assert topic.objectives[0].model_dump() not in goals


def test_goal_payloads_do_not_mutate_the_published_task():
    topic = topics_for("pre-a1").topics[0]
    before = deepcopy(topic.model_dump())
    for skill in SKILLS:
        goals = skill_objectives(topic, skill)
        goals[-1]["nl"] = "Changed by a caller"
    assert topic.model_dump() == before
