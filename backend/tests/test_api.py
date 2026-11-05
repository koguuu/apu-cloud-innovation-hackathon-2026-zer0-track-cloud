import pytest
from helpers import card, healthy_campus, post, trip, wifi

from app.main import create_app


def test_pii_is_rejected(client):
    event = card(1, "lab-ai")
    event["student_id"] = "TP085775"
    r = post(client, event)
    assert r.status_code == 422
    assert r.json()["error"] == "pii_not_allowed" and r.json()["keys"] == ["student_id"]
    nested = wifi("ap-a-01", "block-a")
    nested["metrics"]["email"] = "a@b.com"
    assert post(client, nested).status_code == 422


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e.update(location_id="block-z"),
        lambda e: e.update(student_hash="TP085775"),
        lambda e: e.update(action="teleport"),
        lambda e: e.update(event_type="mystery"),
        lambda e: e.pop("event_id"),
    ],
)
def test_invalid_events_are_rejected_with_details(client, mutate):
    event = card(1, "lab-ai")
    mutate(event)
    r = post(client, event)
    assert r.status_code == 422 and r.json()["error"] == "invalid_event" and r.json()["details"]


def test_out_of_range_metrics_are_rejected(client):
    event = wifi("ap-a-01", "block-a", loss=150)
    assert post(client, event).status_code == 422


def test_bad_json_and_wrong_shape(client):
    assert client.post("/events", content=b"{not json", headers={"content-type": "application/json"}).status_code == 400
    assert client.post("/events", json=[1, 2]).status_code == 422
    assert client.post("/events/batch", json={"a": 1}).status_code == 422


def test_batch_accepts_good_events_and_reports_bad_ones(client):
    bad = card(3, "nowhere")
    dup = card(2, "lab-ai")
    batch = [card(1, "lab-ai"), dup, dup, bad]
    r = client.post("/events/batch", json=batch).json()
    assert r["accepted"] == 2 and r["duplicates"] == 1
    assert r["rejected"][0]["index"] == 3 and r["rejected"][0]["error"] == "invalid_event"
    assert client.get("/zones/lab-ai").json()["seats_free"] == 38


def test_batch_size_limit(client, monkeypatch):
    monkeypatch.setenv("MAX_BATCH", "2")
    r = client.post("/events/batch", json=[card(1, "lab-ai"), card(2, "lab-ai"), card(3, "lab-ai")])
    assert r.status_code == 413


def test_unknown_routes_and_locations(client):
    assert client.get("/zones/block-z").status_code == 404
    assert client.get("/tickets/T-9999").status_code == 404
    assert client.get("/nope").status_code == 404


def test_api_keys(client, monkeypatch):
    monkeypatch.setenv("INGEST_API_KEY", "ingest-secret")
    monkeypatch.setenv("DASHBOARD_API_KEY", "dash-secret")
    event = card(1, "lab-ai")
    assert client.get("/health").status_code == 200  # always open

    assert post(client, event).status_code == 401
    assert client.post("/events", json=event, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/events", json=event, headers={"X-API-Key": "dash-secret"}).status_code == 401
    assert client.post("/events", json=event, headers={"X-API-Key": "ingest-secret"}).status_code == 200

    assert client.get("/state").status_code == 401
    assert client.get("/state", headers={"X-API-Key": "ingest-secret"}).status_code == 401
    assert client.get("/state", headers={"X-API-Key": "dash-secret"}).status_code == 200
    assert client.post("/admin/reset").status_code == 401
    assert client.post("/tickets/T-0001/resolve").status_code == 401


def test_production_refuses_to_start_without_keys(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError):
        create_app()
    monkeypatch.setenv("INGEST_API_KEY", "a")
    monkeypatch.setenv("DASHBOARD_API_KEY", "b")
    create_app()


def test_cors_preflight_for_the_frontend(client):
    r = client.options(
        "/state",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-api-key",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
    blocked = client.options(
        "/state",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in blocked.headers


def test_end_to_end_demo_flow(client, sent):
    """The 3-minute demo: healthy -> kill an AP -> ticket + alert + reroute -> recovery."""
    healthy_campus(client)
    for n in range(1, 11):
        post(client, card(n, "lab-network"))
    before = client.get("/state").json()
    assert before["open_tickets"] == [] and before["best_lab"]

    trip(client, "ap-b-02", "block-b")
    after = client.get("/state").json()
    assert len(after["open_tickets"]) == 1
    assert "Try" in after["active_advisories"][0]["message"]
    assert len(sent) == 1

    for _ in range(3):
        post(client, wifi("ap-b-02", "block-b"))
    final = client.get("/state").json()
    assert final["open_tickets"] == [] and final["active_advisories"] == []
