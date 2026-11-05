import threading

from app import engine, llm

from helpers import healthy_campus, trip

REPLY = '{"explanation": "Gemini words.", "recommended_action": "Do X", "root_cause": "%s", "confidence": "high"}'


def test_ticket_and_alert_do_not_wait_for_gemini(client, monkeypatch, sent):
    monkeypatch.setenv("ENRICH_IN_BACKGROUND", "1")
    release = threading.Event()

    def slow_gemini(prompt, json_mode=False):
        release.wait(5)  # pretend Gemini is slow
        return REPLY % "ap_hardware_failure"

    monkeypatch.setattr(llm, "call_gemini", slow_gemini)
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")

    ticket = client.get("/tickets/T-0001").json()
    assert "100% packet loss" in ticket["explanation"]  # template text, already there
    assert [n.ticket_id for n in sent] == ["T-0001"]    # alert already sent

    release.set()
    engine.wait_for_enrichment()
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["explanation"] == "Gemini words." and ticket["recommended_action"] == "Do X"


def test_gemini_failure_in_background_keeps_template_text(client, monkeypatch):
    monkeypatch.setenv("ENRICH_IN_BACKGROUND", "1")
    monkeypatch.setattr(llm, "call_gemini", lambda prompt, json_mode=False: None)
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    engine.wait_for_enrichment()
    assert "100% packet loss" in client.get("/tickets/T-0001").json()["explanation"]


def test_gemini_can_correct_the_cause_afterwards(client, monkeypatch):
    monkeypatch.setenv("ENRICH_IN_BACKGROUND", "1")
    monkeypatch.setattr(llm, "call_gemini", lambda prompt, json_mode=False: REPLY % "congestion")
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    engine.wait_for_enrichment()
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["root_cause"] == "congestion"
    assert "congested" in client.get("/advisories").json()[0]["message"]
