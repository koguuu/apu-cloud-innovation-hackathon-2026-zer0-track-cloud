"""Detection and ticketing.

A flag only trips after several bad readings in a row (BAD_READINGS_TO_TRIP) and only clears after
several good ones (GOOD_READINGS_TO_RECOVER), so one noisy reading never raises an alert.

Root cause rules (Gemini only writes the explanation, see analyzer.py):
  * many APs bad at once across 2+ locations      -> isp_uplink_outage (campus-wide)
  * bad APs with high clients, low loss, good RSSI -> congestion
  * other bad APs                                  -> ap_hardware_failure
  * IoT device reporting 'down'                    -> iot_device_fault
"""
from __future__ import annotations

import logging
from typing import Optional

from . import models as m
from .analyzer import Draft, explain
from .config import Settings, get_settings
from .health import best_alternative, wifi_health
from .locations import CAPACITY, name_of
from .notifier import send_notification
from .store import ApState, DeviceState, now_iso, store

log = logging.getLogger("engine")

CAUSE_LABEL = {
    "ap_hardware_failure": "AP hardware failure",
    "isp_uplink_outage": "uplink outage",
    "congestion": "Wi-Fi congestion",
    "iot_device_fault": "IoT device fault",
    "unknown": "unknown issue",
}
UPLINK = "isp_uplink_outage"


# ------------------------------------------------------------------ small helpers
def _is_bad(mt: m.Metrics, s: Settings) -> bool:
    return (
        mt.latency_ms >= s.latency_bad_ms
        or mt.packet_loss_pct >= s.loss_bad_pct
        or mt.rssi_dbm <= s.rssi_bad_dbm
    )


def _congested(mt: m.Metrics, s: Settings) -> bool:
    return (
        mt.clients >= s.congestion_clients
        and mt.latency_ms >= s.latency_bad_ms
        and mt.packet_loss_pct < s.loss_bad_pct
        and mt.rssi_dbm > s.rssi_bad_dbm
    )


def _ap_dict(a: ApState) -> dict:
    return {
        "ap_id": a.ap_id,
        "location_id": a.location_id,
        "latency_ms": a.metrics.latency_ms,
        "packet_loss_pct": a.metrics.packet_loss_pct,
        "rssi_dbm": a.metrics.rssi_dbm,
        "clients": a.metrics.clients,
    }


def _open_ticket_by(location_id: Optional[str] = None, cause: Optional[str] = None) -> Optional[m.Ticket]:
    for t in store.tickets.values():
        if t.status != "open":
            continue
        if location_id is not None and t.location_id != location_id:
            continue
        if cause is not None and t.root_cause != cause:
            continue
        return t
    return None


SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _merge(ticket: m.Ticket, d: Draft) -> None:
    ticket.affected_aps = sorted(set(ticket.affected_aps) | set(d.affected_aps))
    ticket.affected_devices = sorted(set(ticket.affected_devices) | set(d.affected_devices))
    sev = _severity(d)  # more APs may have failed since the ticket opened: only ever go up
    if SEVERITY_RANK[sev] > SEVERITY_RANK[ticket.severity]:
        ticket.severity = sev  # type: ignore[assignment]


# ---------------------------------------------------------------- event handlers
def _on_card(e: m.CardAccess) -> None:
    if e.action == "enter":
        for people in store.inside.values():  # a student is in one place at a time
            people.discard(e.student_hash)
        store.inside.setdefault(e.location_id, set()).add(e.student_hash)
    else:
        store.inside.get(e.location_id, set()).discard(e.student_hash)


def _on_wifi(e: m.WifiTelemetry, s: Settings) -> bool:
    """Update AP state. Returns True if this reading tripped the AP's flag."""
    st = store.ap_state.get(e.ap_id)
    if st is None:
        st = ApState(e.ap_id, e.location_id, e.metrics, now_iso())
        store.ap_state[e.ap_id] = st
    st.location_id, st.metrics, st.last_seen = e.location_id, e.metrics, now_iso()

    newly_tripped = False
    if _is_bad(e.metrics, s):
        st.bad_streak, st.good_streak = st.bad_streak + 1, 0
        if not st.tripped and st.bad_streak >= s.bad_readings_to_trip:
            st.tripped = newly_tripped = True
    else:
        st.good_streak, st.bad_streak = st.good_streak + 1, 0
        if st.tripped and st.good_streak >= s.good_readings_to_recover:
            st.tripped = False
    return newly_tripped


def _on_iot(e: m.IotHealth, s: Settings) -> bool:
    """Update device state. Returns True if this reading tripped the device's flag."""
    st = store.devices.get(e.device_id)
    if st is None:
        st = DeviceState(e.device_id, e.location_id, e.device_type, e.status, now_iso())
        store.devices[e.device_id] = st
    st.location_id, st.device_type, st.status, st.last_seen = (
        e.location_id, e.device_type, e.status, now_iso(),
    )
    newly_tripped = False
    if e.status == "down":
        st.bad_streak, st.good_streak = st.bad_streak + 1, 0
        if not st.tripped and st.bad_streak >= s.bad_readings_to_trip:
            st.tripped = newly_tripped = True
    else:
        st.good_streak, st.bad_streak = st.good_streak + 1, 0
        if st.tripped and st.good_streak >= s.good_readings_to_recover:
            st.tripped = False
    return newly_tripped


def _iot_draft(location_id: str) -> Draft:
    down = sorted(d.device_id for d in store.devices.values() if d.location_id == location_id and d.tripped)
    return Draft(
        cause="iot_device_fault",
        location_id=location_id,
        affected_devices=down,
        evidence={
            "devices": [
                {"device_id": d.device_id, "device_type": d.device_type, "status": d.status}
                for d in store.devices.values()
                if d.location_id == location_id and d.tripped
            ],
            "wifi_health": wifi_health(location_id),
        },
    )


def _classify_aps(s: Settings) -> list[Draft]:
    aps = list(store.ap_state.values())
    tripped = [a for a in aps if a.tripped]
    if not tripped:
        return []
    locations = {a.location_id for a in tripped}
    if len(tripped) >= 2 and len(locations) >= 2 and len(tripped) / len(aps) >= s.uplink_fraction:
        return [
            Draft(
                cause=UPLINK,
                location_id="campus",
                affected_aps=sorted(a.ap_id for a in tripped),
                evidence={"tripped": [_ap_dict(a) for a in tripped], "total_aps": len(aps)},
            )
        ]
    drafts = []
    for loc in sorted(locations):
        here = [a for a in tripped if a.location_id == loc]
        healthy = [a for a in aps if a.location_id == loc and not a.tripped]
        cause = "congestion" if all(_congested(a.metrics, s) for a in here) else "ap_hardware_failure"
        drafts.append(
            Draft(
                cause=cause,
                location_id=loc,
                affected_aps=sorted(a.ap_id for a in here),
                evidence={
                    "tripped": [_ap_dict(a) for a in here],
                    "healthy_neighbours": [_ap_dict(a) for a in healthy][:5],
                    "total_aps": len(aps),
                },
            )
        )
    return drafts


def _merge_existing(drafts: list[Draft]) -> list[Draft]:
    """Merge drafts into tickets that are already open; return only genuinely new incidents."""
    new = []
    for d in drafts:
        if d.cause != UPLINK and _open_ticket_by(cause=UPLINK):
            continue  # the campus-wide outage already explains it
        existing = _open_ticket_by(d.location_id, d.cause)
        if existing:
            _merge(existing, d)
        else:
            new.append(d)
    return new


# ----------------------------------------------------------- tickets and messages
def _severity(d: Draft) -> str:
    if d.cause == UPLINK:
        return "high"
    if d.cause == "ap_hardware_failure":
        return "high" if wifi_health(d.location_id) == "down" else "medium"
    if d.cause == "iot_device_fault":
        return "low" if len(d.affected_devices) == 1 else "medium"
    return "medium"


def _advisory_message(t: m.Ticket) -> tuple[str, Optional[str]]:
    place = name_of(t.location_id)
    if t.root_cause == UPLINK:
        return "Campus internet is down. IT has been notified.", None
    issue = {
        "ap_hardware_failure": f"{place} Wi-Fi is degraded",
        "congestion": f"{place} Wi-Fi is congested",
        "iot_device_fault": f"Some devices in {place} are offline",
    }.get(t.root_cause, f"There is a problem in {place}")
    alt = best_alternative({t.location_id})
    if alt is None:
        return f"{issue}. IT has been notified.", None
    health = "stable Wi-Fi" if alt.wifi_health == "good" else "no Wi-Fi alerts"
    return f"{issue}. Try {alt.name} ({alt.seats_free} seats free, {health}).", alt.location_id


def _affected_locations(t: m.Ticket) -> list[str]:
    return sorted(CAPACITY) if t.location_id == "campus" else [t.location_id]


def _open_ticket(d: Draft, explanation: str, action: str) -> Optional[tuple[m.Ticket, m.Advisory, m.Notification]]:
    # Re-check: another request may have opened it while we were waiting for the explanation.
    if d.cause != UPLINK and _open_ticket_by(cause=UPLINK):
        return None
    existing = _open_ticket_by(d.location_id, d.cause)
    if existing:
        _merge(existing, d)
        return None

    ticket_id = store.next_id("T")
    if d.cause == UPLINK:  # the campus-wide ticket replaces per-AP tickets
        for t in store.tickets.values():
            if t.status == "open" and t.root_cause in ("ap_hardware_failure", "congestion"):
                t.status, t.resolved_at = "resolved", now_iso()
                t.resolution_note = f"Superseded by {ticket_id}"
    ticket = m.Ticket(
        ticket_id=ticket_id,
        created_at=now_iso(),
        severity=_severity(d),  # type: ignore[arg-type]
        location_id=d.location_id,
        affected_aps=d.affected_aps,
        affected_devices=d.affected_devices,
        root_cause=d.cause,  # type: ignore[arg-type]
        explanation=explanation,
        recommended_action=action,
    )
    store.tickets[ticket_id] = ticket

    message, suggested = _advisory_message(ticket)
    advisory = m.Advisory(
        advisory_id=store.next_id("A"),
        created_at=now_iso(),
        kind="incident",
        ticket_id=ticket_id,
        message=message,
        affected_locations=_affected_locations(ticket),
        suggested_location=suggested,
    )
    store.advisories.append(advisory)

    what = ", ".join(ticket.affected_aps + ticket.affected_devices)
    text = (
        f"{ticket_id} [{ticket.severity.upper()}] {name_of(ticket.location_id)}: "
        f"{CAUSE_LABEL.get(ticket.root_cause, ticket.root_cause)} ({what}). Action: {action}"
    )[:500]
    notification = m.Notification(
        notification_id=store.next_id("N"), created_at=now_iso(), ticket_id=ticket_id, text=text
    )
    store.notifications.append(notification)
    return ticket, advisory, notification


def _cleared(t: m.Ticket) -> bool:
    if t.root_cause == UPLINK:
        return not any(a.tripped for a in store.ap_state.values())
    if t.root_cause == "iot_device_fault":
        return not any(store.devices[d].tripped for d in t.affected_devices if d in store.devices)
    return not any(store.ap_state[a].tripped for a in t.affected_aps if a in store.ap_state)


def _apply_recoveries() -> list[tuple[m.Ticket, m.Notification]]:
    done = []
    for t in list(store.tickets.values()):
        if t.status != "open" or not _cleared(t):
            continue
        t.status, t.resolved_at = "resolved", now_iso()
        t.resolution_note = "Auto-resolved: readings are back to normal."
        place = name_of(t.location_id)
        store.advisories.append(
            m.Advisory(
                advisory_id=store.next_id("A"),
                created_at=now_iso(),
                kind="recovery",
                ticket_id=t.ticket_id,
                message=f"{place} is back to normal.",
                affected_locations=_affected_locations(t),
            )
        )
        n = m.Notification(
            notification_id=store.next_id("N"),
            created_at=now_iso(),
            ticket_id=t.ticket_id,
            text=f"{t.ticket_id} [RESOLVED] {place}: {CAUSE_LABEL.get(t.root_cause, t.root_cause)} cleared.",
        )
        store.notifications.append(n)
        done.append((t, n))
    return done


def _deliver(n: m.Notification) -> None:
    sent, error = send_notification(n)
    with store.lock:
        n.sent, n.error = sent, error


# ---------------------------------------------------------------------- entry points
def _run(events: list, s: Settings) -> dict:
    """Process events, classifying ONCE at the end, so a burst (e.g. an uplink outage that trips
    many APs in one batch) becomes one incident instead of several short-lived tickets."""
    with store.lock:
        accepted = duplicates = 0
        ap_tripped = False
        iot_locations: set[str] = set()
        for event in events:
            if store.seen(event.event_id):
                duplicates += 1
                continue
            store.mark_seen(event.event_id)
            accepted += 1
            if isinstance(event, m.WifiTelemetry):
                ap_tripped |= _on_wifi(event, s)
            elif isinstance(event, m.CardAccess):
                _on_card(event)
            elif isinstance(event, m.IotHealth):
                if _on_iot(event, s):
                    iot_locations.add(event.location_id)
            else:
                store.lab_activity.append(event)
        drafts: list[Draft] = _classify_aps(s) if ap_tripped else []
        drafts += [_iot_draft(loc) for loc in sorted(iot_locations)]
        drafts = _merge_existing(drafts)

    # Outside the lock: this may call Gemini, which can take seconds.
    explained = [(d, *explain(d)) for d in drafts]

    opened: list[str] = []
    to_send: list[m.Notification] = []
    with store.lock:
        for d, explanation, action in explained:
            made = _open_ticket(d, explanation, action)
            if made:
                opened.append(made[0].ticket_id)
                to_send.append(made[2])
        recovered = _apply_recoveries()
        to_send += [n for _, n in recovered]
        resolved = [t.ticket_id for t, _ in recovered]

    for n in to_send:
        _deliver(n)
    return {"accepted": accepted, "duplicates": duplicates, "tickets_opened": opened, "tickets_resolved": resolved}


def process(event: m.WifiTelemetry | m.CardAccess | m.IotHealth | m.LabActivity) -> dict:
    result = _run([event], get_settings())
    if result["duplicates"]:
        return {"status": "duplicate", "event_id": event.event_id}
    return {
        "status": "accepted",
        "event_id": event.event_id,
        "tickets_opened": result["tickets_opened"],
        "tickets_resolved": result["tickets_resolved"],
    }


def process_batch(events: list) -> dict:
    return _run(events, get_settings())
