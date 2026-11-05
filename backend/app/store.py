"""In-memory state. Fine for the demo (one instance). Firestore can replace this later."""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone

from . import models as m


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ApState:
    ap_id: str
    location_id: str
    metrics: m.Metrics
    last_seen: str
    bad_streak: int = 0
    good_streak: int = 0
    tripped: bool = False


@dataclass
class DeviceState:
    device_id: str
    location_id: str
    device_type: str
    status: str
    last_seen: str
    bad_streak: int = 0
    good_streak: int = 0
    tripped: bool = False


class Store:
    MAX_SEEN = 20000

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.reset()

    def reset(self) -> None:
        with self.lock:
            self.ap_state: dict[str, ApState] = {}
            self.devices: dict[str, DeviceState] = {}
            self.inside: dict[str, set[str]] = {}
            self.lab_activity: list[m.LabActivity] = []
            self.tickets: dict[str, m.Ticket] = {}
            self.advisories: list[m.Advisory] = []
            self.notifications: list[m.Notification] = []
            self._seen: OrderedDict[str, None] = OrderedDict()
            self._counters: dict[str, int] = {}

    def next_id(self, prefix: str) -> str:
        with self.lock:
            n = self._counters.get(prefix, 0) + 1
            self._counters[prefix] = n
            return f"{prefix}-{n:04d}"

    def seen(self, event_id: str) -> bool:
        return event_id in self._seen

    def mark_seen(self, event_id: str) -> None:
        self._seen[event_id] = None
        while len(self._seen) > self.MAX_SEEN:
            self._seen.popitem(last=False)


store = Store()
