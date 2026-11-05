"""Checks the simulator against the data contract and the backend's detection rules.

Run from the repo root:  python -m pytest simulator -q
The contract tests use the backend's own pydantic models, so they need the backend
requirements installed (pip install -r backend/requirements-dev.txt). They skip otherwise.
"""
import random

import pytest

from campus import LATENCY_OK_MAX, LOSS_OK_MAX, RSSI_OK_MIN, Campus
from settings import ALL_APS, AP_LAYOUT, CAPACITY, DEVICES, LABS

# The backend's default "bad" limits (backend/app/config.py).
BAD_LATENCY, BAD_LOSS, BAD_RSSI, CONGESTION_CLIENTS = 150.0, 5.0, -80.0, 150


def make_campus(blip_prob=0.0, seed=1):
    """A campus whose clock we control, so one test can sweep a whole simulated day."""
    now = [0.0]
    campus = Campus(random.Random(seed), day_seconds=100.0, start_hour=7.0, blip_prob=blip_prob, clock=lambda: now[0])
    return campus, now


def is_bad(m):
    return m["latency_ms"] >= BAD_LATENCY or m["packet_loss_pct"] >= BAD_LOSS or m["rssi_dbm"] <= BAD_RSSI


def test_normal_noise_never_looks_bad_over_a_full_day():
    campus, now = make_campus(blip_prob=0.0)
    for tick in range(600):                      # 6 simulated days
        now[0] += 1.0
        for e in campus.wifi_events():
            m = e["metrics"]
            assert not is_bad(m), m
            assert m["latency_ms"] <= LATENCY_OK_MAX and m["packet_loss_pct"] <= LOSS_OK_MAX and m["rssi_dbm"] >= RSSI_OK_MIN
            assert m["clients"] < CONGESTION_CLIENTS


def test_blips_are_isolated_single_readings():
    campus, now = make_campus(blip_prob=0.30, seed=7)     # very noisy on purpose
    streak = {ap: 0 for ap in ALL_APS}
    blips = 0
    for _ in range(2000):
        now[0] += 1.0
        for e in campus.wifi_events():
            ap = e["ap_id"]
            streak[ap] = streak[ap] + 1 if is_bad(e["metrics"]) else 0
            blips += streak[ap] > 0
            assert streak[ap] < 2, f"{ap} had two bad readings in a row from noise alone"
    assert blips > 1000, "expected plenty of blips at this rate"


def test_every_location_has_a_healthy_neighbour():
    assert all(len(aps) >= 2 for aps in AP_LAYOUT.values())
    assert len(set(ALL_APS)) == len(ALL_APS), "ap ids must be unique across the campus"


@pytest.mark.parametrize("mode", ["dead", "degraded"])
def test_fault_modes_are_bad_readings(mode):
    campus, _ = make_campus()
    campus.ap_mode["ap-b-02"] = mode
    for _ in range(50):
        e = next(x for x in campus.wifi_events() if x["ap_id"] == "ap-b-02")
        assert is_bad(e["metrics"])


def test_congestion_matches_the_backends_congestion_rule():
    campus, _ = make_campus()
    campus.congest("block-a")
    for _ in range(50):
        for e in campus.wifi_events():
            if e["location_id"] == "block-a":
                m = e["metrics"]
                assert m["clients"] >= CONGESTION_CLIENTS and m["latency_ms"] >= BAD_LATENCY
                assert m["packet_loss_pct"] < BAD_LOSS and m["rssi_dbm"] > BAD_RSSI


def test_uplink_breaks_every_ap():
    campus, _ = make_campus()
    campus.uplink_outage()
    assert all(mode == "dead" for mode in campus.ap_mode.values())   # 14 of 14, well above the 60% rule


def test_card_events_replay_cleanly_and_respect_capacity():
    campus, now = make_campus()
    inside = {}
    for tick in range(400):
        now[0] += 1.0
        for e in campus.tick_events(tick):
            if e["event_type"] != "card_access":
                continue
            s, lab = e["student_hash"], e["location_id"]
            if e["action"] == "enter":
                assert s not in inside, "student entered while already inside"
                inside[s] = lab
            else:
                assert inside.get(s) == lab, "student exited a lab they were not in"
                del inside[s]
            for l in LABS:
                assert sum(1 for v in inside.values() if v == l) <= CAPACITY[l]


def test_occupancy_rises_and_falls_over_the_day():
    campus, now = make_campus()
    counts = []
    for tick in range(300):
        now[0] += 1.0
        campus.tick_events(tick)
        counts.append(len(campus.inside))
    assert max(counts) - min(counts) >= 20


def test_iot_faulty_device_reports_every_tick_healthy_ones_do_not():
    campus, _ = make_campus()
    campus.iot_fault("reader-net-01")
    ticks_with_event = [t for t in range(1, 4) if any(e["device_id"] == "reader-net-01" for e in campus.iot_events(t))]
    assert ticks_with_event == [1, 2, 3]
    healthy = [t for t in range(1, 4) if any(e["device_id"] == "reader-ai-01" for e in campus.iot_events(t))]
    assert healthy == [1, 2, 3]


def test_commands_validate_their_targets_and_recover_restores_everything():
    campus, _ = make_campus()
    with pytest.raises(ValueError):
        campus.kill_ap("ap-zz-99")
    with pytest.raises(ValueError):
        campus.congest("lab-ai")
    with pytest.raises(ValueError):
        campus.lab_down("block-a")
    campus.kill_ap("ap-b-02")
    campus.iot_fault("reader-net-01")
    assert len(campus.faults()) == 2
    campus.recover("ap-b-02")
    assert campus.faults() == ["reader-net-01=down"]
    campus.recover()
    assert campus.faults() == []


def test_all_events_pass_the_backends_own_validation():
    pytest.importorskip("pydantic")
    try:
        from pydantic import TypeAdapter
        from app.models import Event
        from app.privacy import find_pii_keys
    except ImportError:
        pytest.skip("backend not importable")
    adapter = TypeAdapter(Event)
    campus, now = make_campus(blip_prob=0.05)
    seen_ids = set()
    scenarios = [
        lambda: None,
        lambda: campus.kill_ap("ap-b-02"),
        lambda: campus.degrade_block("block-b"),
        lambda: campus.lab_down("lab-network"),
        lambda: campus.congest("block-a"),
        lambda: campus.uplink_outage(),
        lambda: campus.iot_fault("switch-a-01"),
    ]
    tick = 0
    for scenario in scenarios:
        scenario()
        for _ in range(20):
            now[0] += 1.0
            for event in campus.tick_events(tick):
                assert not find_pii_keys(event)
                adapter.validate_python(event)
                assert event["event_id"] not in seen_ids
                seen_ids.add(event["event_id"])
            tick += 1
        campus.recover()
