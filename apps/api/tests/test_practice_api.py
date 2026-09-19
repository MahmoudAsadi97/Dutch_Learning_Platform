from tests.conftest import auth_headers


def test_mission_endpoints(client, headers):
    listing = client.get("/missions", headers=headers).json()
    assert [m["id"] for m in listing["missions"]] == ["appointment-change"]
    mission = client.get("/missions/appointment-change", headers=headers).json()
    assert mission["fixed_word_count"] < mission["word_limit"]
    assert mission["review"]["unreviewed"] == mission["review"]["total_texts"]
    assert mission["labels"]["unreviewed_nl"] == "Niet-nagekeken inhoud"
    assert [s["key"] for s in mission["document"]["steps"]][0] == "read-reminder"
    step = client.get("/missions/appointment-change/steps/read-reminder", headers=headers).json()["step"]
    assert step["payload"]["type"] == "reading" and len(step["payload"]["questions"]) == 2
    assert client.get("/missions/nope", headers=headers).status_code == 404
    assert client.get("/missions/appointment-change/acceptance/A01", headers=headers).json()["passed"] is True


def test_opening_a_mission_creates_four_skill_records(client, headers):
    client.get("/missions/appointment-change", headers=headers)
    records = client.get("/progress", headers=headers).json()["skill_records"]
    assert sorted(r["skill"] for r in records) == ["listening", "reading", "speaking", "writing"]
    assert all(r["status"] == "not_started" for r in records)


def test_start_session_is_idempotent_and_resumes_the_active_session(client):
    body = {"mission_id": "appointment-change", "variant": "base"}
    first = client.post("/practice/sessions", headers=auth_headers("start-0001"), json=body)
    assert first.status_code == 201
    again = client.post("/practice/sessions", headers=auth_headers("start-0001"), json=body)
    assert again.json()["session"]["id"] == first.json()["session"]["id"]
    # a new request while a session of this variant is active resumes it instead of opening a second one
    other = client.post("/practice/sessions", headers=auth_headers("start-0002"), json=body)
    assert other.json()["session"]["id"] == first.json()["session"]["id"]
    assert first.json()["session"]["current_step_key"] == "read-reminder"
    assert [c["step_key"] for c in first.json()["conversation"]] == ["speak-call"]
    assert first.json()["conversation"][0]["opening_line"].startswith("Goeiedag, Tandartspraktijk")

    transfer = client.post("/practice/sessions", headers=auth_headers("start-0003"),
                           json={"mission_id": "appointment-change", "variant": "transfer"})
    assert transfer.json()["session"]["current_step_key"] == "checkpoint-transfer"
    assert transfer.json()["conversation"][0]["typed_allowed"] is False
    assert transfer.json()["conversation"][0]["help_allowed"] is False

    listing = client.get("/practice/sessions", headers=auth_headers("start-0004")).json()["sessions"]
    assert len(listing) == 2
    only_base = client.get("/practice/sessions", params={"variant": "base", "status": "active"},
                           headers=auth_headers("start-0005")).json()["sessions"]
    assert [s["id"] for s in only_base] == [first.json()["session"]["id"]]

    # after the base session is abandoned a fresh one can be started; the abandoned one keeps its record
    closed = client.post(f"/practice/sessions/{first.json()['session']['id']}/abandon", headers=auth_headers("start-0006"))
    assert closed.status_code == 200 and closed.json()["session"]["status"] == "abandoned"
    fresh = client.post("/practice/sessions", headers=auth_headers("start-0007"), json=body)
    assert fresh.status_code == 201 and fresh.json()["session"]["id"] != first.json()["session"]["id"]


def test_sessions_are_private_to_their_learner(client):
    created = client.post("/practice/sessions", headers=auth_headers("priv-0001"),
                          json={"mission_id": "appointment-change"}).json()["session"]
    mine = client.get(f"/practice/sessions/{created['id']}", headers=auth_headers("priv-0002"))
    assert mine.status_code == 200 and mine.json()["turns"] == [] and mine.json()["evidence"] == []
    someone_else = client.get(f"/practice/sessions/{created['id']}",
                              headers=auth_headers("priv-0003", email="second@example.com"))
    assert someone_else.status_code == 404


def test_preflight_endpoint_never_exposes_secrets(client, headers, settings):
    response = client.get("/health/preflight", headers=headers)
    assert response.status_code == 200
    text = response.text
    assert settings.assertion_signing_key not in text
    assert "dlp:dlp@" not in text
    assert {item["component"] for item in response.json()["items"]} >= {"database", "chat model", "blob store"}


def test_acceptance_checks_run_over_learner_data(client, headers):
    from tests.test_steps import _answer, _start

    session_id = _start(client, "acc-start-0001")
    _answer(client, session_id, "acc-answer-01", "read-reminder", "q-when", 0)
    _answer(client, session_id, "acc-answer-02", "read-reminder", "q-cannot-come", 1)
    client.post(f"/practice/sessions/{session_id}/feedback", headers=auth_headers("acc-feedback-01"),
                json={"step_key": "read-reminder"})
    for turn_id, text in (("acc-turn-01", "Ik moet werken."), ("acc-turn-02", "Donderdag om tien uur is goed."),
                          ("acc-turn-03", "Ja, dat past. Tot dan!")):
        client.post(f"/practice/sessions/{session_id}/turns", headers=auth_headers(turn_id),
                    json={"step_key": "speak-call", "text": text})
    everything = client.get("/missions/appointment-change/acceptance/all", headers=auth_headers("acc-all-0001")).json()
    assert everything["passed"] is True, everything
    assert [c["check_id"] for c in everything["checks"]] == ["A01", "A02", "A03", "A04", "A05", "A06"]
    a03 = next(c for c in everything["checks"] if c["check_id"] == "A03")
    assert any("typed-only" in item["detail"] for item in a03["items"])
    assert client.get("/missions/appointment-change/acceptance/A09", headers=auth_headers("acc-nope-001")).status_code == 404
