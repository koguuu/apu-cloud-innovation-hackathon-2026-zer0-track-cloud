"""HTTP API (Starlette). Run: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import TypeAdapter, ValidationError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import engine
from . import models as m
from .config import get_settings
from .dotenv import load_dotenv
from .health import all_zones, best_alternative, zone
from .locations import CAPACITY
from .privacy import find_pii_keys
from .security import check_key, ensure_safe_config
from .store import now_iso, store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MAX_BODY_BYTES = 1_000_000
_EVENT = TypeAdapter(m.Event)


def _dump(obj: Any) -> Any:
    """Turn pydantic models (also inside lists and dicts) into JSON-safe data."""
    if isinstance(obj, list):
        return [_dump(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else obj


def _guard(request: Request, kind: str) -> Optional[JSONResponse]:
    s = get_settings()
    return check_key(request, s.ingest_api_key if kind == "ingest" else s.dashboard_api_key)


async def _json_body(request: Request) -> tuple[Any, Optional[JSONResponse]]:
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return None, JSONResponse({"error": "body_too_large"}, status_code=413)
    try:
        return await request.json(), None
    except ValueError:
        return None, JSONResponse({"error": "invalid_json"}, status_code=400)


def _parse_event(payload: Any) -> tuple[Optional[Any], Optional[dict]]:
    """Returns (event, error_dict). Rejects anything carrying raw personal identifiers."""
    if not isinstance(payload, dict):
        return None, {"error": "invalid_event", "details": "event must be a JSON object"}
    pii = find_pii_keys(payload)
    if pii:
        return None, {
            "error": "pii_not_allowed",
            "keys": sorted(set(pii)),
            "hint": "identify students with student_hash only",
        }
    try:
        return _EVENT.validate_python(payload), None
    except ValidationError as exc:
        details = [{"loc": [str(x) for x in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
        return None, {"error": "invalid_event", "details": details}


# --------------------------------------------------------------------------- routes
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "time": now_iso()})


async def ingest(request: Request) -> JSONResponse:
    if (denied := _guard(request, "ingest")) is not None:
        return denied
    payload, error = await _json_body(request)
    if error is not None:
        return error
    event, err = _parse_event(payload)
    if err is not None:
        return JSONResponse(err, status_code=422)
    return JSONResponse(await run_in_threadpool(engine.process, event))


async def ingest_batch(request: Request) -> JSONResponse:
    if (denied := _guard(request, "ingest")) is not None:
        return denied
    payload, error = await _json_body(request)
    if error is not None:
        return error
    if not isinstance(payload, list):
        return JSONResponse({"error": "invalid_batch", "details": "body must be a JSON array"}, status_code=422)
    if len(payload) > get_settings().max_batch:
        return JSONResponse({"error": "batch_too_large", "max": get_settings().max_batch}, status_code=413)

    rejected, valid = [], []
    for index, item in enumerate(payload):
        event, err = _parse_event(item)
        if err is not None:
            rejected.append({"index": index, **err})
        else:
            valid.append(event)
    result = await run_in_threadpool(engine.process_batch, valid)
    return JSONResponse({**result, "rejected": rejected})


async def state(request: Request) -> JSONResponse:
    """Everything the frontend needs in one call."""
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    with store.lock:
        open_tickets = [t for t in store.tickets.values() if t.status == "open"]
        active_advisories = [
            a for a in store.advisories
            if a.kind == "incident" and store.tickets[a.ticket_id].status == "open"
        ]
        return JSONResponse(
            _dump(
                {
                    "updated_at": now_iso(),
                    "zones": all_zones(),
                    "best_lab": best_alternative(set()),
                    "open_tickets": open_tickets,
                    "active_advisories": active_advisories,
                    "recent_notifications": list(reversed(store.notifications[-10:])),
                }
            )
        )


async def zones(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    return JSONResponse(_dump(all_zones()))


async def zone_detail(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    location_id = request.path_params["location_id"]
    if location_id not in CAPACITY:
        return JSONResponse({"error": "unknown_location"}, status_code=404)
    return JSONResponse(_dump(zone(location_id)))


async def tickets(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    status = request.query_params.get("status")
    with store.lock:
        items = [t for t in store.tickets.values() if status in (None, t.status)]
        return JSONResponse(_dump(sorted(items, key=lambda t: t.ticket_id, reverse=True)))


async def ticket_detail(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    with store.lock:
        t = store.tickets.get(request.path_params["ticket_id"])
        if t is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        return JSONResponse(_dump(t))


async def ticket_resolve(request: Request) -> JSONResponse:
    """Staff marks a ticket as resolved by hand."""
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    with store.lock:
        t = store.tickets.get(request.path_params["ticket_id"])
        if t is None:
            return JSONResponse({"error": "not_found"}, status_code=404)
        if t.status == "open":
            t.status, t.resolved_at, t.resolution_note = "resolved", now_iso(), "Resolved by staff."
        return JSONResponse(_dump(t))


async def advisories(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    with store.lock:
        return JSONResponse(_dump(list(reversed(store.advisories[-20:]))))


async def notifications(request: Request) -> JSONResponse:
    if (denied := _guard(request, "dashboard")) is not None:
        return denied
    with store.lock:
        return JSONResponse(_dump(list(reversed(store.notifications[-20:]))))


async def admin_reset(request: Request) -> JSONResponse:
    """Clear all state between demo runs."""
    if (denied := _guard(request, "ingest")) is not None:
        return denied
    store.reset()
    return JSONResponse({"status": "reset"})


def create_app() -> Starlette:
    settings = get_settings()
    ensure_safe_config(settings)
    routes = [
        Route("/health", health),
        Route("/events", ingest, methods=["POST"]),
        Route("/events/batch", ingest_batch, methods=["POST"]),
        Route("/state", state),
        Route("/zones", zones),
        Route("/zones/{location_id}", zone_detail),
        Route("/tickets", tickets),
        Route("/tickets/{ticket_id}", ticket_detail),
        Route("/tickets/{ticket_id}/resolve", ticket_resolve, methods=["POST"]),
        Route("/advisories", advisories),
        Route("/notifications", notifications),
        Route("/admin/reset", admin_reset, methods=["POST"]),
    ]
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-API-Key"],
        )
    ]
    return Starlette(routes=routes, middleware=middleware)


load_dotenv()
app = create_app()
