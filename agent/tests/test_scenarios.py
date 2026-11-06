"""Checks the scenario files are well formed and that evaluate.py works. Gemini is faked (no network)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evaluate  # noqa: E402

SCENARIOS = evaluate.load_scenarios()


def test_has_the_four_core_scenarios():
    names = {s["name"] for s in SCENARIOS}
    assert {"ap_failure", "congestion", "uplink_outage", "iot_fault"} <= names


@pytest.mark.parametrize("sc", SCENARIOS, ids=lambda s: s["name"])
def test_scenario_shape(sc):
    for key in ("name", "description", "rule_cause", "expected_cause", "location_id", "evidence"):
        assert key in sc, key
    assert sc["rule_cause"] in evaluate.KNOWN and sc["expected_cause"] in evaluate.KNOWN
    if sc["rule_cause"] == "iot_device_fault":
        assert sc["affected_devices"] and "devices" in sc["evidence"]
    else:
        assert sc["affected_aps"] and "tripped" in sc["evidence"]


def _fake(by_name):
    """Fake Gemini: answers with the cause we choose per scenario, found via the AP/device ids in the prompt."""
    def fake(prompt, *, json_mode=False):
        cause = next(c for key, c in by_name.items() if key in prompt)
        return json.dumps({"root_cause": cause, "confidence": "high",
                           "explanation": "fake explanation", "recommended_action": "fake action"})
    return fake


def test_gemini_can_correct_the_tricky_scenario(monkeypatch):
    analyzer = evaluate.import_analyzer()
    monkeypatch.setattr(analyzer.llm, "call_gemini", _fake({"ap-a-03": "congestion"}))
    sc = next(s for s in SCENARIOS if s["name"] == "ap_looks_like_congestion")
    r = evaluate.run_scenario(sc, analyzer)
    assert r["rules"] == "ap_hardware_failure" and r["gemini"] == "congestion"
    assert r["final"] == "congestion" and r["source"] == "gemini" and evaluate._verdict(r) == "OK"


def test_uplink_cannot_be_overridden(monkeypatch):
    analyzer = evaluate.import_analyzer()
    monkeypatch.setattr(analyzer.llm, "call_gemini", _fake({"ap-a-01": "ap_hardware_failure"}))
    sc = next(s for s in SCENARIOS if s["name"] == "uplink_outage")
    r = evaluate.run_scenario(sc, analyzer)
    assert r["gemini"] == "ap_hardware_failure" and r["final"] == "isp_uplink_outage"
    assert r["source"] == "template (Gemini text discarded)"


def test_no_gemini_falls_back_to_template(monkeypatch):
    analyzer = evaluate.import_analyzer()
    monkeypatch.setattr(analyzer.llm, "call_gemini", lambda p, *, json_mode=False: None)
    for sc in SCENARIOS:
        r = evaluate.run_scenario(sc, analyzer)
        assert r["source"] == "template" and r["final"] == sc["rule_cause"] and r["explanation"]


def test_scenarios_are_not_modified_between_runs(monkeypatch):
    analyzer = evaluate.import_analyzer()
    monkeypatch.setattr(analyzer.llm, "call_gemini", lambda p, *, json_mode=False: None)
    sc = SCENARIOS[0]
    before = json.dumps(sc, sort_keys=True)
    evaluate.run_scenario(sc, analyzer)
    assert json.dumps(sc, sort_keys=True) == before


def test_unsupported_numbers_lint():
    ev = {"tripped": [{"latency_ms": 420, "packet_loss_pct": 1.5, "rssi_dbm": -54, "clients": 52}]}
    ok = "Latency is 420 ms, loss only 1.5% and signal -54 dBm, well under the 5% limit."
    bad = "Congestion ruled out: signal is worse than the -70 dBm threshold, loss below 3%."
    assert evaluate.unsupported_numbers(ok, ev) == []
    found = evaluate.unsupported_numbers(bad, ev)
    assert "-70 dBm" in found and "3 %" in found and 'the word "threshold"' in found


def test_flagged_runs_are_printed_in_full(monkeypatch, capsys):
    analyzer = evaluate.import_analyzer()
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    reply = json.dumps({"root_cause": "ap_hardware_failure", "confidence": "high",
                        "explanation": "Congestion ruled out: worse than the -70 dBm threshold.",
                        "recommended_action": "Replace ap-b-02."})
    monkeypatch.setattr(analyzer.llm, "call_gemini", lambda p, *, json_mode=False: reply)
    evaluate.main(["--delay", "0", "--runs", "2", "ap_failure"])
    out = capsys.readouterr().out
    assert "Flagged explanations" in out and out.count("[ap_failure] not in evidence") == 2
    assert "-70 dBm" in out and "Explanations citing numbers/thresholds not in the evidence: 2/2" in out
