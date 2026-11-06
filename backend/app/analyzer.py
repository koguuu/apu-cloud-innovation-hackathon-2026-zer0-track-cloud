"""Turns a detected incident into plain-English text.

The root cause is decided by rules in engine.py. Gemini only writes the explanation and the
recommended action. If Gemini is unavailable or returns something unusable, template text is used.
Gemini also double-checks the rule cause (prompts/root_cause.md) and can correct AP failure <-> congestion.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import llm
from .locations import name_of

log = logging.getLogger("analyzer")

PROMPT_DIR = Path(__file__).parent / "prompts"
KNOWN_CAUSES = {"ap_hardware_failure", "congestion", "isp_uplink_outage", "iot_device_fault"}
# Gemini may only arbitrate between these two. Uplink and IoT tickets are cleared by engine.py using
# affected_aps / affected_devices, so changing to/from them here would break auto-resolve.
OVERRIDABLE = {"ap_hardware_failure", "congestion"}


@dataclass
class Draft:
    cause: str
    location_id: str
    affected_aps: list[str] = field(default_factory=list)
    affected_devices: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


def _clean(text: object, limit: int) -> str:
    s = re.sub(r"[\x00-\x1f\x7f]+", " ", str(text))
    return re.sub(r"\s+", " ", s).strip()[:limit]


def template(d: Draft) -> tuple[str, str]:
    ev = d.evidence
    place = name_of(d.location_id)
    aps = ", ".join(d.affected_aps)
    tripped = ev.get("tripped", [])
    healthy = ev.get("healthy_neighbours", [])

    if d.cause == "ap_hardware_failure" and tripped:
        worst = max(tripped, key=lambda a: a["packet_loss_pct"])
        plural = "" if len(healthy) == 1 else "s"
        tail = f" while {len(healthy)} other AP{plural} there {'is' if len(healthy) == 1 else 'are'} healthy." if healthy else "."
        return (
            f"{aps} in {place} {'shows' if len(d.affected_aps) == 1 else 'show'} {worst['packet_loss_pct']:.0f}% packet loss and "
            f"{worst['latency_ms']:.0f} ms latency{tail}",
            f"Reboot or replace {aps}; check {'their switch ports' if len(d.affected_aps) > 1 else 'its switch port'} and power.",
        )
    if d.cause == "isp_uplink_outage" and tripped:
        n_locations = len({a["location_id"] for a in tripped})
        return (
            f"{len(d.affected_aps)} of {ev.get('total_aps', '?')} APs across {n_locations} locations "
            "degraded at the same time, which points to a shared uplink or ISP problem and not to "
            "individual APs.",
            "Check the core switch and the ISP link; contact the ISP if the link is down.",
        )
    if d.cause == "congestion" and tripped:
        worst = max(tripped, key=lambda a: a["clients"])
        return (
            f"{aps} in {place} {'have' if len(d.affected_aps) > 1 else 'has'} high latency ({worst['latency_ms']:.0f} ms) with many clients "
            f"({worst['clients']}) but low packet loss and good signal, which points to congestion.",
            "Rebalance clients across nearby APs or add capacity.",
        )
    if d.cause == "iot_device_fault":
        devices = ", ".join(d.affected_devices)
        wifi_ok = ", while Wi-Fi there is healthy" if ev.get("wifi_health") == "good" else ""
        return (
            f"{devices} in {place} stopped reporting{wifi_ok}, which points to a device fault.",
            "Power-cycle or replace the device(s) and check their cabling.",
        )
    return (f"An unexpected problem was detected in {place}.", "Check the affected equipment.")


@lru_cache(maxsize=None)
def _prompt_text(name: str) -> str:
    text = (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()


def _render(name: str, **values: str) -> str:
    text = _prompt_text(name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _maybe_override(d: Draft, cause: object, confidence: object) -> None:
    """Gemini can correct ap_hardware_failure <-> congestion when it is highly confident. Anything
    else keeps the rule engine's cause (the disagreement is logged for review)."""
    if cause not in KNOWN_CAUSES or cause == d.cause:
        return
    if d.cause in OVERRIDABLE and cause in OVERRIDABLE and confidence == "high":
        log.info("Gemini overrides rules: %s -> %s at %s", d.cause, cause, d.location_id)
        d.cause = str(cause)
    else:
        log.info("Gemini suggested %s (%s) but rules say %s at %s; keeping rules",
                 cause, confidence, d.cause, d.location_id)


def _gemini(d: Draft) -> Optional[tuple[str, str]]:
    prompt = _render(
        "root_cause",
        location=name_of(d.location_id),
        rule_cause=d.cause,
        evidence=json.dumps(d.evidence),
    )
    raw = llm.call_gemini(prompt, json_mode=True)
    if not raw:
        return None
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        explanation = _clean(data["explanation"], 400)
        action = _clean(data["recommended_action"], 200)
    except (ValueError, KeyError, TypeError):
        return None
    if not (explanation and action):
        return None
    cause = data.get("root_cause")
    _maybe_override(d, cause, data.get("confidence"))
    if cause in KNOWN_CAUSES and cause != d.cause:
        # The ticket keeps a different cause than Gemini argued for, so its text would contradict the
        # ticket (e.g. "replace the AP hardware" on an uplink outage). Use the template instead.
        log.info("Gemini text discarded: written for %s, ticket cause is %s", cause, d.cause)
        return None
    return explanation, action


def explain(d: Draft) -> tuple[str, str]:
    """Returns (explanation, recommended_action). May correct d.cause (see _maybe_override).
    If Gemini is unavailable or unusable, template text is used and the rule cause stands."""
    return _gemini(d) or template(d)
