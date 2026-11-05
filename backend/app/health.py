"""Zone status: seats free (from card events) plus Wi-Fi/IoT health (from probes)."""
from __future__ import annotations

from typing import Optional

from . import models as m
from .locations import CAPACITY, LAB_IDS, name_of
from .store import now_iso, store

HEALTH_FACTOR = {"good": 1.0, "degraded": 0.4, "down": 0.0, "unknown": 0.5}


def occupancy(location_id: str) -> int:
    return len(store.inside.get(location_id, ()))


def _uplink_down() -> bool:
    return any(
        t.status == "open" and t.root_cause == "isp_uplink_outage" for t in store.tickets.values()
    )


def wifi_health(location_id: str) -> str:
    with store.lock:
        if _uplink_down():
            return "down"
        aps = [a for a in store.ap_state.values() if a.location_id == location_id]
        if not aps:
            return "unknown"
        tripped = [a for a in aps if a.tripped]
        if len(tripped) == len(aps):
            return "down"
        if tripped:
            return "degraded"
        return "good"


def devices_down(location_id: str) -> int:
    with store.lock:
        return sum(1 for d in store.devices.values() if d.location_id == location_id and d.tripped)


def zone(location_id: str) -> m.ZoneStatus:
    with store.lock:
        total = CAPACITY[location_id]
        free = max(0, total - occupancy(location_id))
        health = wifi_health(location_id)
        down = devices_down(location_id)
        score = 0.5 * (free / total) + 0.5 * HEALTH_FACTOR[health] - 0.15 * down
        return m.ZoneStatus(
            location_id=location_id,
            name=name_of(location_id),
            updated_at=now_iso(),
            seats_total=total,
            seats_free=free,
            wifi_health=health,  # type: ignore[arg-type]
            iot_devices_down=down,
            score=round(max(0.0, min(1.0, score)), 2),
        )


def all_zones() -> list[m.ZoneStatus]:
    return [zone(loc) for loc in CAPACITY]


def best_alternative(exclude: set[str]) -> Optional[m.ZoneStatus]:
    """Best lab with free seats and no Wi-Fi alert, other than the excluded locations."""
    candidates = [zone(loc) for loc in LAB_IDS if loc not in exclude]
    candidates = [z for z in candidates if z.seats_free > 0 and z.wifi_health in ("good", "unknown")]
    return max(candidates, key=lambda z: z.score, default=None)
