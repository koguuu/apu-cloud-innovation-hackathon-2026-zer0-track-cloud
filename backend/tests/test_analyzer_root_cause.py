"""Gemini root-cause step in app/analyzer.py. Gemini is faked, no network."""
import json

import pytest

from app import analyzer, llm
from app.analyzer import Draft, explain


def _ap_draft(cause="ap_hardware_failure"):
    return Draft(
        cause=cause, location_id="block-b", affected_aps=["ap-b-02"],
        evidence={"tripped": [{"ap_id": "ap-b-02", "location_id": "block-b", "latency_ms": 900,
                               "packet_loss_pct": 100, "rssi_dbm": -90, "clients": 3}],
                  "healthy_neighbours": [{"ap_id": "ap-b-01", "latency_ms": 20}], "total_aps": 6})


def _fake(monkeypatch, **fields):
    reply = {"root_cause": "ap_hardware_failure", "confidence": "high",
             "explanation": "ap-b-02 has 100% loss; neighbours healthy so not congestion.",
             "recommended_action": "Reboot ap-b-02."}
    reply.update(fields)
    seen = {}

    def fake(prompt, *, json_mode=False):
        seen["prompt"] = prompt
        return json.dumps(reply)
    monkeypatch.setattr(llm, "call_gemini", fake)
    return seen


def test_prompt_comes_from_file_and_has_evidence(monkeypatch):
    seen = _fake(monkeypatch)
    explain(_ap_draft())
    assert "Rule engine's guess: ap_hardware_failure" in seen["prompt"]
    assert "ap-b-02" in seen["prompt"] and "{{" not in seen["prompt"] and "<!--" not in seen["prompt"]


def test_agreement_keeps_cause_and_uses_gemini_text(monkeypatch):
    _fake(monkeypatch)
    d = _ap_draft()
    explanation, action = explain(d)
    assert d.cause == "ap_hardware_failure" and "not congestion" in explanation and action == "Reboot ap-b-02."


def test_high_confidence_can_correct_ap_vs_congestion(monkeypatch):
    _fake(monkeypatch, root_cause="congestion", confidence="high")
    d = _ap_draft()
    explain(d)
    assert d.cause == "congestion"


def test_low_confidence_does_not_override(monkeypatch):
    _fake(monkeypatch, root_cause="congestion", confidence="medium")
    d = _ap_draft()
    explain(d)
    assert d.cause == "ap_hardware_failure"


@pytest.mark.parametrize("rule,gemini", [("isp_uplink_outage", "ap_hardware_failure"),
                                         ("ap_hardware_failure", "isp_uplink_outage"),
                                         ("iot_device_fault", "ap_hardware_failure"),
                                         ("ap_hardware_failure", "iot_device_fault")])
def test_uplink_and_iot_never_overridden(monkeypatch, rule, gemini):
    _fake(monkeypatch, root_cause=gemini, confidence="high")
    d = _ap_draft(rule)
    explain(d)
    assert d.cause == rule


def test_invented_cause_ignored(monkeypatch):
    _fake(monkeypatch, root_cause="aliens", confidence="high")
    d = _ap_draft()
    explain(d)
    assert d.cause == "ap_hardware_failure"


def test_old_style_reply_without_cause_still_works(monkeypatch):
    monkeypatch.setattr(llm, "call_gemini", lambda p, *, json_mode=False:
                        '{"explanation": "e", "recommended_action": "a"}')
    d = _ap_draft()
    assert explain(d) == ("e", "a") and d.cause == "ap_hardware_failure"


@pytest.mark.parametrize("bad", [None, "", "not json", '{"explanation": "only"}', '{"explanation": "", "recommended_action": ""}'])
def test_gemini_failure_uses_template_and_keeps_cause(monkeypatch, bad):
    monkeypatch.setattr(llm, "call_gemini", lambda p, *, json_mode=False: bad)
    d = _ap_draft()
    explanation, action = explain(d)
    assert d.cause == "ap_hardware_failure" and "ap-b-02" in explanation and action


# ---- template wording (used when Gemini is unavailable) ----
def _template_draft(cause, aps):
    ev = {"tripped": [{"ap_id": a, "location_id": "block-b", "latency_ms": 900, "packet_loss_pct": 100,
                       "rssi_dbm": -90, "clients": 60} for a in aps], "healthy_neighbours": [], "total_aps": 6}
    return Draft(cause=cause, location_id="block-b", affected_aps=list(aps), evidence=ev)


def test_template_ap_failure_one_ap_says_its_switch_port():
    _, action = analyzer.template(_template_draft("ap_hardware_failure", ["ap-b-02"]))
    assert "its switch port" in action and "their" not in action


def test_template_ap_failure_two_aps_say_their_switch_ports():
    _, action = analyzer.template(_template_draft("ap_hardware_failure", ["ap-b-01", "ap-b-02"]))
    assert "their switch ports" in action and "its switch port" not in action


def test_template_congestion_has_vs_have():
    one, _ = analyzer.template(_template_draft("congestion", ["ap-b-01"]))
    two, _ = analyzer.template(_template_draft("congestion", ["ap-b-01", "ap-b-02"]))
    assert "ap-b-01 in" in one and " has high latency" in one
    assert " have high latency" in two


# ---- Gemini text must never contradict the ticket's cause ----
def test_text_discarded_when_gemini_disagrees_and_cause_is_kept(monkeypatch):
    _fake(monkeypatch, root_cause="ap_hardware_failure", confidence="high",
          explanation="Replace the failing AP hardware.", recommended_action="Dispatch a technician.")
    d = _ap_draft("isp_uplink_outage")
    explanation, action = explain(d)
    assert d.cause == "isp_uplink_outage"
    assert "Replace the failing AP" not in explanation and "technician" not in action
    assert "uplink" in explanation.lower()


def test_text_kept_when_override_applied(monkeypatch):
    _fake(monkeypatch, root_cause="congestion", confidence="high",
          explanation="High load, low loss.", recommended_action="Balance clients.")
    d = _ap_draft("ap_hardware_failure")
    assert explain(d) == ("High load, low loss.", "Balance clients.") and d.cause == "congestion"


def test_text_discarded_when_low_confidence_disagreement(monkeypatch):
    _fake(monkeypatch, root_cause="congestion", confidence="medium",
          explanation="It is congestion.", recommended_action="Add capacity.")
    d = _ap_draft("ap_hardware_failure")
    explanation, _ = explain(d)
    assert d.cause == "ap_hardware_failure" and "It is congestion." not in explanation
