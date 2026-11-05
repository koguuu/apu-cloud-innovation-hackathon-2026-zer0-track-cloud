"""Gemini access behind ONE function. Swap this (e.g. to Gemini Enterprise) without touching the rest.

Uses the public REST API with the standard library only. Returns None on any failure,
so callers always have a fallback.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .config import get_settings

log = logging.getLogger("llm")


def _call_model(model_name: str, prompt: str, json_mode: bool, key: str, timeout: float) -> Optional[str]:
    """One model, one retry on a temporary overload (429/500/503)."""
    model = urllib.parse.quote(model_name, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config: dict = {"temperature": 0.2}
    if json_mode:
        config["responseMimeType"] = "application/json"
    body = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config}
    ).encode("utf-8")
    for attempt in (1, 2):
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": key},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as exc:
            log.warning("Gemini %s: HTTP %s (attempt %d)", model_name, exc.code, attempt)
            if exc.code not in (429, 500, 503) or attempt == 2:
                return None
            time.sleep(1.0)
        except Exception as exc:  # network, bad JSON... never crash ingest
            log.warning("Gemini %s failed (%s)", model_name, type(exc).__name__)
            return None
    return None


def call_gemini(prompt: str, *, json_mode: bool = False) -> Optional[str]:
    s = get_settings()
    if not s.gemini_api_key:
        log.info("GEMINI_API_KEY is not set, using template text")
        return None
    models = [s.gemini_model] + ([s.gemini_fallback_model] if s.gemini_fallback_model else [])
    for name in models:
        text = _call_model(name, prompt, json_mode, s.gemini_api_key, s.gemini_timeout_s)
        if text:
            return text
    log.warning("Gemini unavailable, using template text")
    return None
