"""Gemini access behind ONE function. Swap this (e.g. to Gemini Enterprise) without touching the rest.

Uses the public REST API with the standard library only. Returns None on any failure,
so callers always have a fallback.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Optional

from .config import get_settings

log = logging.getLogger("llm")


def call_gemini(prompt: str, *, json_mode: bool = False) -> Optional[str]:
    s = get_settings()
    if not s.gemini_api_key:
        return None
    model = urllib.parse.quote(s.gemini_model, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    config: dict = {"temperature": 0.2}
    if json_mode:
        config["responseMimeType"] = "application/json"
    body = json.dumps(
        {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "x-goog-api-key": s.gemini_api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=s.gemini_timeout_s) as resp:
            data = json.load(resp)
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:  # network, quota, bad JSON... never crash ingest
        log.warning("Gemini call failed (%s), using template text", type(exc).__name__)
        return None
