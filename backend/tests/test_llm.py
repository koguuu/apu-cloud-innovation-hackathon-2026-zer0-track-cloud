import io
import urllib.error

from app import llm


def _http(code):
    return urllib.error.HTTPError("u", code, "x", {}, io.BytesIO(b"{}"))


class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


OK = b'{"candidates":[{"content":{"parts":[{"text":"hi"}]}}]}'


def test_no_key_returns_none(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert llm.call_gemini("x") is None


def test_retries_once_on_503(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    calls = []

    def fake(req, timeout=0):
        calls.append(1)
        if len(calls) == 1:
            raise _http(503)
        return _Resp(OK)

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    assert llm.call_gemini("x") == "hi" and len(calls) == 2


def test_falls_back_to_second_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_MODEL", "m1")
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "m2")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    seen = []

    def fake(req, timeout=0):
        seen.append(req.full_url)
        if "m1" in req.full_url:
            raise _http(404)
        return _Resp(OK)

    monkeypatch.setattr(llm.urllib.request, "urlopen", fake)
    assert llm.call_gemini("x") == "hi"
    assert "m1" in seen[0] and "m2" in seen[-1]
