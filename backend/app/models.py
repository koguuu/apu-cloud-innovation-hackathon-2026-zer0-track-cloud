"""Data contract (see docs/event-schema.md). Input events and output objects."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .locations import CAPACITY

STUDENT_HASH_PATTERN = r"^s_[0-9a-f]{8,64}$"


def _known_location(value: str) -> str:
    if value not in CAPACITY:
        raise ValueError(f"unknown location_id '{value}', expected one of {sorted(CAPACITY)}")
    return value


# ---------------------------------------------------------------- input events
class Metrics(BaseModel):
    latency_ms: float = Field(ge=0)
    packet_loss_pct: float = Field(ge=0, le=100)
    rssi_dbm: float = Field(ge=-120, le=0)
    clients: int = Field(default=0, ge=0)


class WifiTelemetry(BaseModel):
    event_type: Literal["wifi_telemetry"]
    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    location_id: str
    ap_id: str = Field(min_length=1, max_length=50)
    metrics: Metrics
    syslog: list[str] = Field(default_factory=list, max_length=50)

    _loc = field_validator("location_id")(_known_location)


class CardAccess(BaseModel):
    event_type: Literal["card_access"]
    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    location_id: str
    student_hash: str = Field(pattern=STUDENT_HASH_PATTERN)
    action: Literal["enter", "exit"]

    _loc = field_validator("location_id")(_known_location)


class IotHealth(BaseModel):
    event_type: Literal["iot_health"]
    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    location_id: str
    device_id: str = Field(min_length=1, max_length=50)
    device_type: Literal["card_reader", "sensor", "switch"]
    status: Literal["ok", "degraded", "down"]
    detail: str = Field(default="", max_length=200)

    _loc = field_validator("location_id")(_known_location)


class LabActivity(BaseModel):
    """Stretch (Lab Record). Stored only."""

    event_type: Literal["lab_activity"]
    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    student_hash: str = Field(pattern=STUDENT_HASH_PATTERN)
    lab_type: Literal["ai", "cybersecurity", "networking", "iot"]
    module_id: str = Field(min_length=1, max_length=50)
    status: Literal["started", "in_progress", "completed"]
    minutes_spent: int = Field(ge=0, le=1440)


Event = Annotated[
    Union[WifiTelemetry, CardAccess, IotHealth, LabActivity],
    Field(discriminator="event_type"),
]

# --------------------------------------------------------------- output objects
RootCause = Literal[
    "ap_hardware_failure", "isp_uplink_outage", "congestion", "iot_device_fault", "unknown"
]


class Ticket(BaseModel):
    ticket_id: str
    created_at: str
    severity: Literal["low", "medium", "high"]
    location_id: str
    affected_aps: list[str] = Field(default_factory=list)
    affected_devices: list[str] = Field(default_factory=list)
    root_cause: RootCause
    explanation: str
    recommended_action: str
    status: Literal["open", "resolved"] = "open"
    resolved_at: Optional[str] = None
    resolution_note: Optional[str] = None


class Advisory(BaseModel):
    advisory_id: str
    created_at: str
    kind: Literal["incident", "recovery"]
    ticket_id: str
    message: str
    affected_locations: list[str]
    suggested_location: Optional[str] = None


class Notification(BaseModel):
    notification_id: str
    created_at: str
    channel: Literal["telegram"] = "telegram"
    ticket_id: str
    text: str
    sent: bool = False
    error: Optional[str] = None


class ZoneStatus(BaseModel):
    location_id: str
    name: str
    updated_at: str
    seats_total: int
    seats_free: int
    wifi_health: Literal["good", "degraded", "down", "unknown"]
    iot_devices_down: int = 0
    score: float
