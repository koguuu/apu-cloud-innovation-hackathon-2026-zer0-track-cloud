"""Tiny HTTP client for the backend (standard library only, so nothing extra to install)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import List
from urllib.parse import urlparse

LOOPBACK = {"localhost", "127.0.0.1", "::1"}


class ApiError(Exception):
    """The backend answered with an error status (401, 413, 422, ...)."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"HTTP {status}: {body[:300]}")
        self.status = status
        self.body = body


class BackendUnreachable(Exception):
    """Could not connect (backend not running, wrong URL, network down)."""


class Client:
    def __init__(self, base_url: str, api_key: str = "", timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        host = urlparse(self.base_url).hostname or ""
        # Never send local traffic through a system proxy.
        self._opener = (
            urllib.request.build_opener(urllib.request.ProxyHandler({}))
            if host in LOOPBACK
            else urllib.request.build_opener()
        )

    def _call(self, method: str, path: str, payload=None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(self.base_url + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        if self.api_key:
            request.add_header("X-API-Key", self.api_key)
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:   # must come before URLError (it is a subclass)
            raise ApiError(exc.code, exc.read().decode("utf-8", "replace")) from None
        except (urllib.error.URLError, OSError) as exc:
            raise BackendUnreachable(str(exc)) from None

    def health(self) -> dict:
        return self._call("GET", "/health")

    def reset(self) -> dict:
        return self._call("POST", "/admin/reset")

    def send_batch(self, events: List[dict]) -> dict:
        return self._call("POST", "/events/batch", events)
