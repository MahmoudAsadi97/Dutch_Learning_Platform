def test_level_references_keep_bridges_and_provisional_content_separate(client, headers):
    response = client.get("/curriculum/pre-b1/alignment", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["reference_status"] == "internal_bridge"
    assert set(body["skills"]) == {"reading", "listening", "speaking", "writing"}
    assert body["review"]["content_calibrated"] is False
    assert body["source_details"]
    assert "learner_key" not in body


def test_exam_catalog_and_c2_gap_do_not_create_certificates(client, headers):
    response = client.get("/curriculum/reference/exams", headers=headers)
    assert response.status_code == 200
    profiles = response.json()["profiles"]
    assert len(profiles) == 11
    assert all(profile["recognized_certificate"] is False for profile in profiles)
    assert not any("C2" in profile["levels"] for profile in profiles)
    assert client.get("/curriculum/a3/alignment", headers=headers).status_code == 404


def test_reference_routes_still_require_identity(client):
    assert client.get("/curriculum/a2/alignment").status_code == 401
    assert client.get("/curriculum/reference/exams").status_code == 401
