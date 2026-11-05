from helpers import (
    bad_wifi, card, healthy_campus, iot, post, student, trip, wifi,
)


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_flag_only_trips_after_three_bad_readings(client, sent):
    healthy_campus(client)
    for _ in range(2):
        assert post(client, bad_wifi("ap-b-02", "block-b")).json()["tickets_opened"] == []
    assert client.get("/tickets").json() == []

    result = post(client, bad_wifi("ap-b-02", "block-b")).json()
    assert result["tickets_opened"] == ["T-0001"]

    ticket = client.get("/tickets/T-0001").json()
    assert ticket["root_cause"] == "ap_hardware_failure"
    assert ticket["location_id"] == "block-b"
    assert ticket["affected_aps"] == ["ap-b-02"]
    assert ticket["severity"] == "medium"  # the other Block B AP is healthy
    assert "ap-b-02" in ticket["explanation"] and "100% packet loss" in ticket["explanation"]
    assert "1 other AP" in ticket["explanation"]
    assert ticket["status"] == "open"

    advisory = client.get("/advisories").json()[0]
    assert advisory["kind"] == "incident" and advisory["ticket_id"] == "T-0001"
    assert advisory["message"].startswith("Block B Wi-Fi is degraded. Try ")
    assert "seats free" in advisory["message"]
    assert advisory["suggested_location"].startswith("lab-")

    assert len(sent) == 1 and "ap-b-02" in sent[0].text
    assert client.get("/notifications").json()[0]["sent"] is True


def test_one_noisy_reading_in_between_resets_the_count(client):
    healthy_campus(client)
    post(client, bad_wifi("ap-b-02", "block-b"))
    post(client, bad_wifi("ap-b-02", "block-b"))
    post(client, wifi("ap-b-02", "block-b"))  # good reading resets the streak
    post(client, bad_wifi("ap-b-02", "block-b"))
    post(client, bad_wifi("ap-b-02", "block-b"))
    assert client.get("/tickets").json() == []


def test_no_duplicate_ticket_while_still_failing(client):
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b", times=3)
    for _ in range(5):
        assert post(client, bad_wifi("ap-b-02", "block-b")).json()["tickets_opened"] == []
    assert len(client.get("/tickets").json()) == 1


def test_auto_recovery_after_three_good_readings(client, sent):
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    post(client, wifi("ap-b-02", "block-b"))
    post(client, wifi("ap-b-02", "block-b"))
    assert client.get("/tickets/T-0001").json()["status"] == "open"
    result = post(client, wifi("ap-b-02", "block-b")).json()
    assert result["tickets_resolved"] == ["T-0001"]

    ticket = client.get("/tickets/T-0001").json()
    assert ticket["status"] == "resolved" and ticket["resolved_at"]
    kinds = [a["kind"] for a in client.get("/advisories").json()]
    assert kinds == ["recovery", "incident"]  # newest first
    assert len(sent) == 2 and "[RESOLVED]" in sent[1].text


def test_uplink_outage_supersedes_single_ap_tickets(client):
    healthy_campus(client)
    trip(client, "ap-a-01", "block-a")
    trip(client, "ap-b-01", "block-b")
    trip(client, "ap-b-02", "block-b")
    trip(client, "ap-n-01", "lab-network")

    open_tickets = client.get("/tickets?status=open").json()
    assert len(open_tickets) == 1
    uplink = open_tickets[0]
    assert uplink["root_cause"] == "isp_uplink_outage"
    assert uplink["location_id"] == "campus" and uplink["severity"] == "high"
    assert "ap-n-01" in uplink["affected_aps"]
    resolved = client.get("/tickets?status=resolved").json()
    assert resolved and all("Superseded by" in t["resolution_note"] for t in resolved)

    advisory = client.get("/advisories").json()[0]
    assert advisory["message"].startswith("Campus internet is down")
    assert all(z["wifi_health"] == "down" for z in client.get("/zones").json()
               if z["location_id"] in ("block-a", "block-b", "lab-network", "lab-iot"))

    # everything recovers
    for ap, loc in [("ap-a-01", "block-a"), ("ap-b-01", "block-b"), ("ap-b-02", "block-b"), ("ap-n-01", "lab-network")]:
        for _ in range(3):
            post(client, wifi(ap, loc))
    assert client.get("/tickets?status=open").json() == []
    assert client.get("/zones/block-b").json()["wifi_health"] == "good"


def test_congestion_is_not_reported_as_hardware_failure(client):
    healthy_campus(client)
    for _ in range(3):
        post(client, wifi("ap-n-01", "lab-network", latency=400, loss=0.5, rssi=-60, clients=200))
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["root_cause"] == "congestion"
    assert "congestion" in ticket["explanation"]


def test_single_ap_location_down_is_high_severity(client):
    healthy_campus(client)
    trip(client, "ap-i-01", "lab-iot")  # the only AP in the IoT lab
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["severity"] == "high"
    assert client.get("/zones/lab-iot").json()["wifi_health"] == "down"


def test_iot_device_fault(client):
    healthy_campus(client)
    for _ in range(2):
        assert post(client, iot("reader-iot-01", "lab-iot", "down")).json()["tickets_opened"] == []
    assert post(client, iot("reader-iot-01", "lab-iot", "down")).json()["tickets_opened"] == ["T-0001"]
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["root_cause"] == "iot_device_fault"
    assert ticket["affected_devices"] == ["reader-iot-01"] and ticket["severity"] == "low"
    assert "Wi-Fi there is healthy" in ticket["explanation"]
    assert client.get("/zones/lab-iot").json()["iot_devices_down"] == 1

    for _ in range(3):
        post(client, iot("reader-iot-01", "lab-iot", "ok"))
    assert client.get("/tickets/T-0001").json()["status"] == "resolved"
    assert client.get("/zones/lab-iot").json()["iot_devices_down"] == 0


def test_occupancy_from_card_events(client):
    for n in (1, 2, 3):
        post(client, card(n, "lab-network"))
    assert client.get("/zones/lab-network").json()["seats_free"] == 37
    post(client, card(1, "lab-network", "exit"))
    assert client.get("/zones/lab-network").json()["seats_free"] == 38
    # a student can only be in one place: entering the AI lab leaves the networking lab
    post(client, card(2, "lab-ai"))
    assert client.get("/zones/lab-network").json()["seats_free"] == 39
    assert client.get("/zones/lab-ai").json()["seats_free"] == 39


def test_seats_never_negative(client):
    for n in range(1, 60):
        post(client, card(n, "lab-iot"))
    zone = client.get("/zones/lab-iot").json()
    assert zone["seats_free"] == 0 and zone["seats_total"] == 40


def test_duplicate_event_id_is_ignored(client):
    event = card(1, "lab-ai")
    assert post(client, event).json()["status"] == "accepted"
    assert post(client, event).json()["status"] == "duplicate"
    assert client.get("/zones/lab-ai").json()["seats_free"] == 39


def test_advisory_points_to_a_healthy_lab_with_seats(client):
    healthy_campus(client)
    for n in range(1, 41):
        post(client, card(n, "lab-network"))  # networking lab is full
    trip(client, "ap-b-02", "block-b")
    advisory = client.get("/advisories").json()[0]
    assert advisory["suggested_location"] != "lab-network"


def test_state_has_everything_the_frontend_needs(client):
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    data = client.get("/state").json()
    assert set(data) == {
        "updated_at", "zones", "best_lab", "open_tickets", "active_advisories", "recent_notifications",
    }
    assert len(data["zones"]) == 7
    assert data["best_lab"]["location_id"].startswith("lab-")
    assert len(data["open_tickets"]) == 1 and len(data["active_advisories"]) == 1


def test_staff_can_resolve_a_ticket_and_reset_clears_state(client):
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    r = client.post("/tickets/T-0001/resolve").json()
    assert r["status"] == "resolved" and r["resolution_note"] == "Resolved by staff."
    assert client.post("/tickets/T-9999/resolve").status_code == 404
    assert client.post("/admin/reset").json() == {"status": "reset"}
    assert client.get("/tickets").json() == []
    assert client.get("/zones/block-b").json()["wifi_health"] == "unknown"


def test_lab_activity_is_stored_for_the_stretch_module(client):
    event = {
        "event_type": "lab_activity", "event_id": "la-1", "timestamp": "2026-11-05T12:00:00Z",
        "student_hash": student(7), "lab_type": "cybersecurity", "module_id": "net-sec-03",
        "status": "completed", "minutes_spent": 45,
    }
    assert post(client, event).json()["status"] == "accepted"
    from app.store import store
    assert len(store.lab_activity) == 1


def _bad_round(aps):
    return [bad_wifi(ap, loc) for ap, loc in aps]


def test_batch_classifies_once_so_an_uplink_outage_is_one_ticket(client, sent):
    healthy_campus(client)
    aps = [("ap-a-01", "block-a"), ("ap-b-01", "block-b"), ("ap-b-02", "block-b"), ("ap-n-01", "lab-network")]
    events = []
    for _ in range(3):  # three readings from every AP, sent as one batch
        events += _bad_round(aps)
    r = client.post("/events/batch", json=events)
    assert r.status_code == 200
    assert len(r.json()["tickets_opened"]) == 1

    tickets = client.get("/tickets").json()
    assert len(tickets) == 1 and tickets[0]["root_cause"] == "isp_uplink_outage"
    assert [n.ticket_id for n in sent] == ["T-0001"]  # one Telegram alert, not four


def test_batch_degrading_a_whole_block_is_high_severity(client):
    healthy_campus(client)
    events = []
    for _ in range(3):
        events += _bad_round([("ap-b-01", "block-b"), ("ap-b-02", "block-b")])
    client.post("/events/batch", json=events)
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["severity"] == "high"
    assert ticket["affected_aps"] == ["ap-b-01", "ap-b-02"]


def test_severity_goes_up_when_more_aps_fail_later(client):
    healthy_campus(client)
    trip(client, "ap-b-01", "block-b")
    assert client.get("/tickets/T-0001").json()["severity"] == "medium"
    trip(client, "ap-b-02", "block-b")  # the rest of the block now fails too
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["severity"] == "high" and len(client.get("/tickets").json()) == 1
