"""Known locations (must match docs/event-schema.md)."""
from __future__ import annotations

CAPACITY: dict[str, int] = {
    "block-a": 120,
    "block-b": 120,
    "library": 200,
    "lab-ai": 40,
    "lab-cyber": 40,
    "lab-network": 40,
    "lab-iot": 40,
}

NAMES: dict[str, str] = {
    "block-a": "Block A",
    "block-b": "Block B",
    "library": "Library",
    "lab-ai": "AI Lab",
    "lab-cyber": "Cybersecurity Lab",
    "lab-network": "Networking Lab",
    "lab-iot": "IoT Lab",
    "campus": "Campus",
}

# Places a student can be sent to when something fails.
LAB_IDS: tuple[str, ...] = ("lab-ai", "lab-cyber", "lab-network", "lab-iot")


def name_of(location_id: str) -> str:
    return NAMES.get(location_id, location_id)
