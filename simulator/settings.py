"""Settings and the fixed campus layout.

The layout must match docs/event-schema.md and backend/app/locations.py.
Settings come from environment variables. A .env file is also read, but only
for the keys listed in ENV_KEYS (so the simulator never loads secrets it does not need).
Order of priority: real environment variables, then simulator/.env, then <repo>/.env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

# ---------------------------------------------------------------- campus layout
CAPACITY = {
    "block-a": 120,
    "block-b": 120,
    "library": 200,
    "lab-ai": 40,
    "lab-cyber": 40,
    "lab-network": 40,
    "lab-iot": 40,
}
BLOCKS = ("block-a", "block-b")
LABS = ("lab-ai", "lab-cyber", "lab-network", "lab-iot")

# Access point ids must be unique across the whole campus (the backend keys APs by ap_id).
# Every location has at least 2 APs so a single-AP fault has healthy neighbours.
AP_LAYOUT = {
    "block-a": ["ap-a-01", "ap-a-02", "ap-a-03"],
    "block-b": ["ap-b-01", "ap-b-02", "ap-b-03"],
    "lab-ai": ["ap-ai-01", "ap-ai-02"],
    "lab-cyber": ["ap-cyber-01", "ap-cyber-02"],
    "lab-network": ["ap-net-01", "ap-net-02"],
    "lab-iot": ["ap-iot-01", "ap-iot-02"],
    "library": ["ap-lib-01", "ap-lib-02"],
}
AP_LOCATION = {ap: loc for loc, aps in AP_LAYOUT.items() for ap in aps}
ALL_APS = list(AP_LOCATION)

# device_id -> (location_id, device_type). device_type: card_reader, sensor or switch.
DEVICES = {
    "reader-ai-01": ("lab-ai", "card_reader"),
    "reader-cyber-01": ("lab-cyber", "card_reader"),
    "reader-net-01": ("lab-network", "card_reader"),
    "reader-iot-01": ("lab-iot", "card_reader"),
    "sensor-iot-01": ("lab-iot", "sensor"),
    "switch-a-01": ("block-a", "switch"),
    "switch-b-01": ("block-b", "switch"),
}

# ---------------------------------------------------------------------- settings
ENV_KEYS = (
    "BACKEND_URL",
    "INGEST_API_KEY",
    "SIM_TICK_SECONDS",
    "SIM_DAY_SECONDS",
    "SIM_START_HOUR",
    "SIM_BLIP_PROB",
    "SIM_SEED",
)


def _read_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key in ENV_KEYS and value:
            values[key] = value
    return values


def _file_values() -> Dict[str, str]:
    merged = _read_env_file(REPO_ROOT / ".env")
    merged.update(_read_env_file(HERE / ".env"))  # simulator/.env wins over the repo .env
    return merged


@dataclass(frozen=True)
class Settings:
    backend_url: str
    api_key: str
    tick_seconds: float      # one reading per AP every tick
    day_seconds: float       # how many real seconds one simulated day (07:00-21:00) lasts
    start_hour: float        # simulated hour of day when the run starts
    blip_prob: float         # chance of a single noisy reading per AP per tick
    seed: Optional[int]


def load_settings() -> Settings:
    files = _file_values()

    def get(name: str, default: str) -> str:
        return os.environ.get(name) or files.get(name) or default

    def number(name: str, default: float) -> float:
        try:
            return float(get(name, str(default)))
        except ValueError:
            return default

    seed_text = get("SIM_SEED", "")
    return Settings(
        backend_url=get("BACKEND_URL", "http://localhost:8000").rstrip("/"),
        api_key=get("INGEST_API_KEY", ""),
        tick_seconds=max(0.1, number("SIM_TICK_SECONDS", 2.0)),
        day_seconds=max(10.0, number("SIM_DAY_SECONDS", 240.0)),
        start_hour=min(20.9, max(7.0, number("SIM_START_HOUR", 9.5))),
        blip_prob=min(1.0, max(0.0, number("SIM_BLIP_PROB", 0.0))),
        seed=int(seed_text) if seed_text.lstrip("-").isdigit() else None,
    )
