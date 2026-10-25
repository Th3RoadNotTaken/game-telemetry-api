def valid_event():
    return {
        "encounter": "boss",
        "run_id": "t",
        "player_id": "p1",
        "player_style": "aggressive",
        "attempt": 1,
        "won": False,
        "duration_s": 63.2,
    }

def test_post_event_returns_201_and_the_stored_row(client):
    response = client.post("/events", json=valid_event())
    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["encounter"] == "boss"
    assert body["created_at"] is not None

def test_post_event_rejects_negative_duration(client):
    response = client.post("/events", json={**valid_event(), "duration_s": -1})
    assert response.status_code == 422

def test_bulk_post_with_one_bad_row_stores_nothing(client):
    bad = {**valid_event(), "attempt": 0}
    response = client.post("/events/bulk", json=[valid_event(), bad])
    assert response.status_code == 422
    report = client.get("/encounters/boss/report", params={"run_id": "t"})
    assert report.status_code == 404