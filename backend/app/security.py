"""API-key checks. Keys are optional in dev, required when APP_ENV=production."""
from __future__ import annotations

import secrets
from typing import Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import Settings


def ensure_safe_config(s: Settings) -> None:
    """Refuse to start in production without keys (an open ingest endpoint would be abused)."""
    if s.app_env == "production" and not (s.ingest_api_key and s.dashboard_api_key):
        raise RuntimeError("APP_ENV=production requires INGEST_API_KEY and DASHBOARD_API_KEY")


def check_key(request: Request, expected: str) -> Optional[JSONResponse]:
    """Return a 401 response if the X-API-Key header does not match, else None."""
    if not expected:  # dev mode: no key configured
        return None
    given = request.headers.get("x-api-key", "")
    if given and secrets.compare_digest(given.encode(), expected.encode()):
        return None
    return JSONResponse({"error": "unauthorized"}, status_code=401)
