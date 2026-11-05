import uuid

TS = "2026-11-05T10:15:30Z"


def _id() -> str:
    return str(uuid.uuid4())


def student(n: int) -> str:
    return f"s_{n:08x}"


def wifi(ap, loc, latency=30, loss=0.2, rssi=-55, clients=40):
    return {
        "event_type": "wifi_telemetry", "event_id": _id(), "timestamp": TS,
        "location_id": loc, "ap_id": ap,
        "metrics": {"latency_ms": latency, "packet_loss_pct": loss, "rssi_dbm": rssi, "clients": clients},
        "syslog": [],
    }


def bad_wifi(ap, loc):
    return wifi(ap, loc, latency=900, loss=100, rssi=-90)


def card(n, loc, action="enter"):
    return {
        "event_type": "card_access", "event_id": _id(), "timestamp": TS,
        "location_id": loc, "student_hash": student(n), "action": action,
    }


def iot(device, loc, status="ok"):
    return {
        "event_type": "iot_health", "event_id": _id(), "timestamp": TS,
        "location_id": loc, "device_id": device, "device_type": "card_reader",
        "status": status, "detail": "",
    }


def post(client, event):
    return client.post("/events", json=event)


def healthy_campus(client):
    """One or two healthy APs in several places."""
    for ap, loc in [
        ("ap-a-01", "block-a"), ("ap-b-01", "block-b"), ("ap-b-02", "block-b"),
        ("ap-n-01", "lab-network"), ("ap-i-01", "lab-iot"),
    ]:
        assert post(client, wifi(ap, loc)).status_code == 200


def trip(client, ap, loc, times=3):
    last = None
    for _ in range(times):
        last = post(client, bad_wifi(ap, loc)).json()
    return last
