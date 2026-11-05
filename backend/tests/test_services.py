import json
import logging
import urllib.error

import pytest
from helpers import healthy_campus, trip

from app import llm, notifier
from app import models as m
from app.privacy import find_pii_keys, hash_student_id


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self, *args):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _notification():
    return m.Notification(notification_id="N-1", created_at="t", ticket_id="T-1", text="hello admin")


# ----------------------------------------------------------------------- Gemini
def test_gemini_text_is_used_when_it_is_valid(client, monkeypatch):
    monkeypatch.setattr(
        llm, "call_gemini",
        lambda prompt, json_mode=False: '{"explanation": "Custom words.\\n\\nSecond line", "recommended_action": "Do X"}',
    )
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    ticket = client.get("/tickets/T-0001").json()
    assert ticket["explanation"] == "Custom words. Second line"
    assert ticket["recommended_action"] == "Do X"
    assert ticket["root_cause"] == "ap_hardware_failure"  # rules decide the cause, not the LLM


@pytest.mark.parametrize("reply", [None, "not json at all", '{"explanation": "only one key"}', '{"explanation": "", "recommended_action": ""}'])
def test_template_text_is_used_when_gemini_fails_or_is_unusable(client, monkeypatch, reply):
    monkeypatch.setattr(llm, "call_gemini", lambda prompt, json_mode=False: reply)
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    assert "100% packet loss" in client.get("/tickets/T-0001").json()["explanation"]


def test_gemini_is_not_called_for_every_reading(client, monkeypatch):
    calls = []
    monkeypatch.setattr(llm, "call_gemini", lambda prompt, json_mode=False: calls.append(1))
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b", times=10)
    assert len(calls) == 1


def test_call_gemini_without_key_does_nothing(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network must not be used without a key")
    monkeypatch.setattr(llm.urllib.request, "urlopen", boom)
    assert llm.call_gemini("hi") is None


def test_call_gemini_request_shape(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "key-123")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"], seen["headers"], seen["body"] = req.full_url, dict(req.header_items()), json.loads(req.data)
        return FakeResponse({"candidates": [{"content": {"parts": [{"text": "answer"}]}}]})

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake_urlopen)
    assert llm.call_gemini("question", json_mode=True) == "answer"
    assert "key-123" not in seen["url"]  # key travels in a header, never in the URL
    assert seen["headers"]["X-goog-api-key"] == "key-123"
    assert seen["body"]["contents"][0]["parts"][0]["text"] == "question"
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_call_gemini_failure_returns_none(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "key-123")

    def fail(*a, **k):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(llm.urllib.request, "urlopen", fail)
    assert llm.call_gemini("hi") is None


# --------------------------------------------------------------------- notifier
def test_not_configured_means_not_sent():
    notifier.set_sender(None)
    assert notifier.send_notification(_notification()) == (False, "telegram_not_configured")


def test_telegram_success(monkeypatch):
    notifier.set_sender(None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"], seen["data"] = req.full_url, req.data.decode()
        return FakeResponse({"ok": True})

    monkeypatch.setattr(notifier.urllib.request, "urlopen", fake_urlopen)
    assert notifier.send_notification(_notification()) == (True, None)
    assert seen["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert "chat_id=42" in seen["data"] and "hello+admin" in seen["data"]


def test_telegram_failure_never_leaks_the_token(monkeypatch, caplog):
    notifier.set_sender(None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:secret-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    def fail(*a, **k):
        raise urllib.error.URLError("https://api.telegram.org/bot123:secret-token/sendMessage")

    monkeypatch.setattr(notifier.urllib.request, "urlopen", fail)
    with caplog.at_level(logging.INFO):
        assert notifier.send_notification(_notification()) == (False, "URLError")
    assert "secret-token" not in caplog.text


def test_custom_sender_and_its_failure(client):
    notifier.set_sender(lambda n: True)
    assert notifier.send_notification(_notification()) == (True, None)

    def broken(n):
        raise RuntimeError("boom")

    notifier.set_sender(broken)
    assert notifier.send_notification(_notification()) == (False, "RuntimeError")


def test_failed_delivery_is_visible_on_the_notification(client):
    notifier.set_sender(lambda n: False)
    healthy_campus(client)
    trip(client, "ap-b-02", "block-b")
    assert client.get("/notifications").json()[0]["sent"] is False


# ---------------------------------------------------------------------- privacy
def test_student_hash_is_stable_anonymous_and_valid(monkeypatch):
    monkeypatch.setenv("HASH_SALT", "pepper")
    a = hash_student_id("TP085775")
    assert a == hash_student_id(" tp085775 ")  # case and spaces do not matter
    assert a != hash_student_id("TP000001")
    assert "085775" not in a
    assert m.CardAccess(
        event_type="card_access", event_id="1", timestamp="2026-11-05T10:00:00Z",
        location_id="lab-ai", student_hash=a, action="enter",
    )


def test_hashing_requires_a_salt():
    with pytest.raises(ValueError):
        hash_student_id("TP085775")


def test_find_pii_keys_looks_inside_nested_data():
    assert find_pii_keys({"a": [{"Email": "x"}], "b": {"student_id": 1}}) == ["Email", "student_id"]
    assert find_pii_keys({"student_hash": "s_00000001"}) == []
