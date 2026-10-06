"""What the exercise engine must preserve (roadmap P3) and what it will consciously change (step 5.5).

These pin today's behaviour of the practice payloads so that the engine work cannot drift it by accident:
- the final check withholds keys, samples and the listening transcript (never changes);
- topic detail strips the keys of the activity being practised until it is submitted;
- the stage view and the library story detail still send practice keys to the browser today
  (step 5.5 removes them once grammar, the lesson and Story Time run on the engine);
- core-lesson practice explanations carry no answer_index; the export carries no keys.
"""

from __future__ import annotations

import json

from dlp.domains.curriculum.service import curriculum


def _first_stage_id() -> str:
    return curriculum().stages[0].id


def test_stage_view_still_sends_practice_keys_today(client, headers):
    view = client.get(f"/curriculum/{_first_stage_id()}", headers=headers).json()
    grammar_questions = [q for item in view["grammar"] for q in item["practice"]]
    assert grammar_questions and all("answer_index" in q and "explanation" in q for q in grammar_questions)
    assert all("answer_index" in q for q in view["lesson"]["reading_questions"])
    assert "test" not in view  # the final check never travels with the stage


def test_topic_detail_withholds_the_practised_activity_keys(client, headers):
    stage_id = _first_stage_id()
    page = client.get(f"/curriculum/{stage_id}/topics", headers=headers, params={"skill": "reading"}).json()
    topic_id = page["items"][0]["id"]
    detail = client.get(f"/curriculum/{stage_id}/topics/{topic_id}", headers=headers, params={"skill": "reading"})
    assert detail.status_code == 200
    body = detail.json()
    assert body["activity"]["questions"] and all("answer_index" not in q and "explanation" not in q
                                                 for q in body["activity"]["questions"])
    assert len(body["vocabulary"]) >= 1 and all("term" in w and "meaning" in w and "example" in w for w in body["vocabulary"])


def test_library_story_detail_still_sends_its_key_today(client, headers):
    stage_id = _first_stage_id()
    stories = client.get(f"/library/{stage_id}/stories", headers=headers).json()
    story_id = stories["items"][0]["id"]
    detail = client.get(f"/library/{stage_id}/stories/{story_id}", headers=headers).json()
    assert "answer_index" in detail["question"]


def test_core_practice_explanations_carry_no_key_and_the_export_none_at_all(client, headers):
    stage = curriculum().stages[0]
    answers = {q.id: q.answer_index for q in stage.lesson.reading_questions}
    response = client.post(f"/curriculum/{stage.id}/practice", headers=headers,
                           json={"skill": "reading", "answers": answers, "text": ""})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["passed"] is True and body["completed"] is True
    assert body["explanations"] and all("answer_index" not in item for item in body["explanations"])
    export = client.get("/export", headers=headers).json()
    assert "answer_index" not in json.dumps(export["curriculum"])
