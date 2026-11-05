"""Settings. Read from environment variables on every call, so tests can change them."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in os.getenv(name, default).split(",") if x.strip())


@dataclass(frozen=True)
class Settings:
    # security
    app_env: str
    ingest_api_key: str
    dashboard_api_key: str
    cors_origins: tuple[str, ...]
    # Gemini (optional: without a key the agent uses template text)
    gemini_api_key: str
    gemini_model: str
    gemini_fallback_model: str
    gemini_timeout_s: float
    # Telegram (optional: without these, notifications are logged and marked not sent)
    telegram_bot_token: str
    telegram_chat_id: str
    # detection thresholds
    latency_bad_ms: float
    loss_bad_pct: float
    rssi_bad_dbm: float
    congestion_clients: int
    bad_readings_to_trip: int
    good_readings_to_recover: int
    uplink_fraction: float
    max_batch: int


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        ingest_api_key=os.getenv("INGEST_API_KEY", ""),
        dashboard_api_key=os.getenv("DASHBOARD_API_KEY", ""),
        cors_origins=_csv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        gemini_fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", ""),
        gemini_timeout_s=_float("GEMINI_TIMEOUT_S", 8.0),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        latency_bad_ms=_float("LATENCY_BAD_MS", 150.0),
        loss_bad_pct=_float("LOSS_BAD_PCT", 5.0),
        rssi_bad_dbm=_float("RSSI_BAD_DBM", -80.0),
        congestion_clients=_int("CONGESTION_CLIENTS", 150),
        bad_readings_to_trip=_int("BAD_READINGS_TO_TRIP", 3),
        good_readings_to_recover=_int("GOOD_READINGS_TO_RECOVER", 3),
        uplink_fraction=_float("UPLINK_FRACTION", 0.6),
        max_batch=_int("MAX_BATCH", 500),
    )
