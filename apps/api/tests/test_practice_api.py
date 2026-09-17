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


def test_start_session_is_idempotent_per_request_id(client):
    body = {"mission_id": "appointment-change", "variant": "base"}
    first = client.post("/practice/sessions", headers=auth_headers("start-0001"), json=body)
    assert first.status_code == 201
    again = client.post("/practice/sessions", headers=auth_headers("start-0001"), json=body)
    assert again.json()["session"]["id"] == first.json()["session"]["id"]
    other = client.post("/practice/sessions", headers=auth_headers("start-0002"), json=body)
    assert other.json()["session"]["id"] != first.json()["session"]["id"]
    assert first.json()["session"]["current_step_key"] == "read-reminder"

    transfer = client.post("/practice/sessions", headers=auth_headers("start-0003"),
                           json={"mission_id": "appointment-change", "variant": "transfer"})
    assert transfer.json()["session"]["current_step_key"] == "checkpoint-transfer"

    listing = client.get("/practice/sessions", headers=auth_headers("start-0004")).json()["sessions"]
    assert len(listing) == 3


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
