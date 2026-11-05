"""Generates the simulated campus data: Wi-Fi probes, IoT heartbeats and card-reader events.

Everything here returns plain dicts shaped like docs/event-schema.md.
Nothing in this file talks to the network (that is client.py), so it is easy to test.

How the "bad" limits line up with the backend (backend/app/config.py):
  a reading is bad if latency >= 150 ms, packet loss >= 5 % or RSSI <= -80 dBm.
  Normal readings are clamped well inside those limits. The only exception is an occasional
  single "blip" (see blip_prob), and an AP never blips twice in a row. So noise alone can
  never raise an alert, because the backend needs 3 bad readings in a row from the same AP.
"""
from __future__ import annotations

import hashlib
import math
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from settings import ALL_APS, AP_LAYOUT, AP_LOCATION, BLOCKS, CAPACITY, DEVICES, LABS

STUDENT_POOL = 220          # fake students (more than the 160 lab seats)
IOT_EVERY = 3               # healthy devices report every 3rd tick; faulty ones report every tick
LAB_FACTOR = {"lab-ai": 0.90, "lab-cyber": 0.75, "lab-network": 0.80, "lab-iot": 0.60}
MAX_OCCUPANCY = 0.90        # labs never fill completely, so the student page always has a free seat
CLIENTS_PER_AP_AT_PEAK = 85  # block APs; the congestion limit in the backend is 150

# Normal-noise limits (kept clear of the backend's bad limits: 150 ms, 5 %, -80 dBm).
LATENCY_OK_MAX = 110.0
LOSS_OK_MAX = 2.5
RSSI_OK_MIN = -72

AP_MODES = ("ok", "dead", "degraded", "congested")
DEVICE_STATUSES = ("ok", "degraded", "down")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Campus:
    def __init__(
        self,
        rng: Optional[random.Random] = None,
        day_seconds: float = 240.0,
        start_hour: float = 9.5,
        blip_prob: float = 0.01,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.rng = rng or random.Random()
        self.day_seconds = day_seconds
        self.start_hour = start_hour
        self.blip_prob = blip_prob
        self._clock = clock
        self._t0 = clock()
        # Anonymous student ids: "s_" + 10 hex characters (the backend accepts 8-64).
        self.students = [
            "s_" + hashlib.sha256(f"sim-student-{i}".encode()).hexdigest()[:10]
            for i in range(STUDENT_POOL)
        ]
        self.reset()

    # ------------------------------------------------------------------ state
    def reset(self) -> None:
        """Back to a healthy campus with nobody inside (used at start and by the reset command)."""
        self.ap_mode: Dict[str, str] = {ap: "ok" for ap in ALL_APS}
        self.device_status: Dict[str, str] = {dev: "ok" for dev in DEVICES}
        self.inside: Dict[str, str] = {}      # student_hash -> lab they are in
        self._blipped: Dict[str, bool] = {ap: False for ap in ALL_APS}   # did this AP blip last tick?
        self._warm_up = True                  # first tick fills the labs straight away

    def faults(self) -> List[str]:
        """Human-readable list of everything that is not healthy right now."""
        items = [f"{ap}={mode}" for ap, mode in self.ap_mode.items() if mode != "ok"]
        items += [f"{dev}={status}" for dev, status in self.device_status.items() if status != "ok"]
        return items

    # ------------------------------------------------------------- daily pattern
    def sim_hour(self) -> float:
        """Simulated hour of day, 7.0 to 21.0, repeating every day_seconds of real time."""
        span = 14.0
        offset = (self.start_hour - 7.0) / span * self.day_seconds
        fraction = (((self._clock() - self._t0) + offset) % self.day_seconds) / self.day_seconds
        return 7.0 + fraction * span

    @staticmethod
    def load(hour: float) -> float:
        """0.15 (quiet) to 1.0 (busy): a morning peak at 10:30 and an afternoon peak at 15:00."""
        morning = math.exp(-(((hour - 10.5) / 1.8) ** 2))
        afternoon = math.exp(-(((hour - 15.0) / 2.0) ** 2))
        return 0.15 + 0.85 * max(morning, afternoon)

    # --------------------------------------------------------------------- events
    def _base(self, event_type: str) -> dict:
        return {"event_type": event_type, "event_id": str(uuid.uuid4()), "timestamp": _now_iso()}

    def tick_events(self, tick: int) -> List[dict]:
        """Everything to send for one tick. APs are listed block by block (see README note on uplink)."""
        step = 999 if self._warm_up else 2
        self._warm_up = False
        events = self.wifi_events()
        events += self.iot_events(tick)
        events += self.card_events(step)
        return events

    # ---------------------------------------------------------------------- wifi
    def _metrics(self, ap_id: str, load: float) -> Tuple[dict, List[str]]:
        rng = self.rng
        location = AP_LOCATION[ap_id]
        mode = self.ap_mode[ap_id]

        if location in LABS:
            people = sum(1 for lab in self.inside.values() if lab == location)
            base_clients = people * 2.0 / len(AP_LAYOUT[location])   # about 2 devices per student
        else:
            base_clients = CLIENTS_PER_AP_AT_PEAK * load
        clients = max(0, int(base_clients * rng.uniform(0.85, 1.15)) + rng.randint(0, 3))

        if mode == "dead":
            latency, loss, rssi, clients = rng.uniform(700, 1500), 100.0, rng.randint(-95, -90), rng.randint(0, 3)
            syslog = [f"{ap_id}: uplink lost", f"{ap_id}: beacon timeout"]
        elif mode == "degraded":
            latency, loss, rssi = rng.uniform(250, 600), rng.uniform(15, 40), rng.randint(-88, -82)
            syslog = [f"{ap_id}: high retry rate", f"{ap_id}: weak signal"]
        elif mode == "congested":
            clients = rng.randint(160, 230)
            latency, loss, rssi = rng.uniform(180, 320), rng.uniform(0.5, 3.0), rng.randint(-68, -52)
            syslog = [f"{ap_id}: client limit reached"]
        else:
            latency = _clamp(rng.gauss(32 + 14 * load, 7), 12.0, LATENCY_OK_MAX)
            loss = _clamp(abs(rng.gauss(0.3, 0.3)), 0.0, LOSS_OK_MAX)
            rssi = int(_clamp(rng.gauss(-58, 4), RSSI_OK_MIN, -45))
            syslog = [f"{ap_id}: client assoc ok"]
            # A blip is one noisy reading. Never two in a row from the same AP, so noise alone
            # can never reach the backend's "3 bad readings in a row" trip rule.
            if not self._blipped[ap_id] and rng.random() < self.blip_prob:
                latency = rng.uniform(160, 240)
                syslog = [f"{ap_id}: latency spike"]
                self._blipped[ap_id] = True
            else:
                self._blipped[ap_id] = False
            return self._pack(latency, loss, rssi, clients), syslog

        self._blipped[ap_id] = False
        return self._pack(latency, loss, rssi, clients), syslog

    @staticmethod
    def _pack(latency: float, loss: float, rssi: float, clients: int) -> dict:
        return {
            "latency_ms": round(latency, 1),
            "packet_loss_pct": round(loss, 2),
            "rssi_dbm": int(rssi),
            "clients": clients,
        }

    def wifi_events(self) -> List[dict]:
        load = self.load(self.sim_hour())
        events = []
        for location, aps in AP_LAYOUT.items():
            for ap_id in aps:
                metrics, syslog = self._metrics(ap_id, load)
                event = self._base("wifi_telemetry")
                event.update(location_id=location, ap_id=ap_id, metrics=metrics, syslog=syslog)
                events.append(event)
        return events

    # ----------------------------------------------------------------------- iot
    def iot_events(self, tick: int) -> List[dict]:
        details = {"ok": "heartbeat ok", "degraded": "slow response", "down": "no heartbeat"}
        events = []
        for device_id, (location, device_type) in DEVICES.items():
            status = self.device_status[device_id]
            if status == "ok" and tick % IOT_EVERY != 0:
                continue
            event = self._base("iot_health")
            event.update(
                location_id=location,
                device_id=device_id,
                device_type=device_type,
                status=status,
                detail=details[status],
            )
            events.append(event)
        return events

    # ---------------------------------------------------------------------- cards
    def _card(self, lab: str, student: str, action: str) -> dict:
        event = self._base("card_access")
        event.update(location_id=lab, student_hash=student, action=action)
        return event

    def card_events(self, step: int = 2) -> List[dict]:
        """Move each lab towards its target occupancy, at most `step` students per tick."""
        load = self.load(self.sim_hour())
        outside = [s for s in self.students if s not in self.inside]
        events = []
        for lab in LABS:
            target = round(CAPACITY[lab] * min(MAX_OCCUPANCY, load * LAB_FACTOR[lab])) + self.rng.randint(-1, 1)
            target = int(_clamp(target, 0, CAPACITY[lab]))
            here = [s for s, where in self.inside.items() if where == lab]
            if len(here) < target:
                for _ in range(min(step, target - len(here))):
                    if not outside:
                        break
                    student = outside.pop(self.rng.randrange(len(outside)))
                    self.inside[student] = lab
                    events.append(self._card(lab, student, "enter"))
            elif len(here) > target:
                for student in self.rng.sample(here, min(step, len(here) - target)):
                    del self.inside[student]
                    events.append(self._card(lab, student, "exit"))
        return events

    # --------------------------------------------------------------------- faults
    def _need_ap(self, ap_id: str) -> None:
        if ap_id not in self.ap_mode:
            raise ValueError(f"unknown AP '{ap_id}'. Try one of: {', '.join(ALL_APS)}")

    def kill_ap(self, ap_id: str) -> str:
        self._need_ap(ap_id)
        self.ap_mode[ap_id] = "dead"
        return f"{ap_id} is dead (100% loss). Expect an ap_hardware_failure ticket in about 3 ticks."

    def degrade_block(self, block: str) -> str:
        if block not in BLOCKS:
            raise ValueError(f"degrade-block needs one of: {', '.join(BLOCKS)}")
        for ap in AP_LAYOUT[block]:
            self.ap_mode[ap] = "degraded"
        return f"all APs in {block} are degraded. Expect one ap_hardware_failure ticket."

    def lab_down(self, lab: str) -> str:
        if lab not in LABS:
            raise ValueError(f"lab-down needs one of: {', '.join(LABS)}")
        for ap in AP_LAYOUT[lab]:
            self.ap_mode[ap] = "dead"
        return f"{lab} network is down (all its APs dead). Expect one ap_hardware_failure ticket."

    def uplink_outage(self) -> str:
        for ap in ALL_APS:
            self.ap_mode[ap] = "dead"
        return "campus uplink outage (every AP dead). Expect a campus-wide isp_uplink_outage ticket (see README note)."

    def congest(self, block: str) -> str:
        if block not in BLOCKS:
            raise ValueError(f"congestion needs a block: {', '.join(BLOCKS)} (labs only have 40 seats)")
        for ap in AP_LAYOUT[block]:
            self.ap_mode[ap] = "congested"
        return f"{block} is congested (150+ clients per AP). Expect a congestion ticket."

    def iot_fault(self, device_id: str) -> str:
        if device_id not in self.device_status:
            raise ValueError(f"unknown device '{device_id}'. Try one of: {', '.join(DEVICES)}")
        self.device_status[device_id] = "down"
        return f"{device_id} reports down. Expect an iot_device_fault ticket in about 3 ticks."

    def recover(self, target: Optional[str] = None) -> str:
        """target: nothing/'all', an AP id, a device id or a location id."""
        if target in (None, "", "all"):
            for ap in self.ap_mode:
                self.ap_mode[ap] = "ok"
            for dev in self.device_status:
                self.device_status[dev] = "ok"
            return "everything is healthy again. Tickets resolve after 3 good readings."
        if target in self.ap_mode:
            self.ap_mode[target] = "ok"
            return f"{target} is healthy again."
        if target in self.device_status:
            self.device_status[target] = "ok"
            return f"{target} is healthy again."
        if target in AP_LAYOUT:
            for ap in AP_LAYOUT[target]:
                self.ap_mode[ap] = "ok"
            for dev, (location, _) in DEVICES.items():
                if location == target:
                    self.device_status[dev] = "ok"
            return f"{target} is healthy again."
        raise ValueError(f"nothing called '{target}' to recover")
