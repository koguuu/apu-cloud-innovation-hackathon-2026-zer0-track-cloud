# Data contract (shared by everyone)

This is the one format everyone builds against so we can work in parallel.
**Change it only after telling the group.** All timestamps are ISO 8601 UTC.

Campus Health uses `wifi_telemetry`, `card_access`, `iot_health`, `ticket`, `advisory`, `notification` and `zone_status`.
`lab_activity` (stretch) is accepted and stored. The source of truth is `backend/app/models.py`.

## Locations

| `location_id` | Name | Capacity (seats) |
|---|---|---|
| `block-a` | Block A | 120 |
| `block-b` | Block B | 120 |
| `library` | Library (optional) | 200 |
| `lab-ai` | AI Lab | 40 |
| `lab-cyber` | Cybersecurity Lab | 40 |
| `lab-network` | Networking Lab | 40 |
| `lab-iot` | IoT Lab | 40 |

Access points use ids like `ap-b-02` (block, number).

## Input events (simulator -> backend)

### `wifi_telemetry`

```json
{
  "event_type": "wifi_telemetry",
  "event_id": "6f1c2e9a-0b1d-4a52-9c1e-2d6a7e4f1a10",
  "timestamp": "2026-11-05T10:15:30Z",
  "location_id": "block-b",
  "ap_id": "ap-b-02",
  "metrics": {
    "latency_ms": 42,
    "packet_loss_pct": 0.5,
    "rssi_dbm": -58,
    "clients": 87
  },
  "syslog": ["ap-b-02: client assoc ok"]
}
```

### `card_access`

```json
{
  "event_type": "card_access",
  "event_id": "b3d1f0c4-77a2-4d0e-8f43-1a2b3c4d5e6f",
  "timestamp": "2026-11-05T10:15:31Z",
  "location_id": "lab-network",
  "student_hash": "s_9f2c41ab",
  "action": "enter"
}
```

`action` is `enter` or `exit`.

### `iot_health`

```json
{
  "event_type": "iot_health",
  "event_id": "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d",
  "timestamp": "2026-11-05T10:15:32Z",
  "location_id": "lab-iot",
  "device_id": "reader-iot-01",
  "device_type": "card_reader",
  "status": "ok",
  "detail": "heartbeat ok"
}
```

`device_type`: `card_reader`, `sensor`, `switch`. `status`: `ok`, `degraded`, `down`.

### `lab_activity` (stretch)

```json
{
  "event_type": "lab_activity",
  "event_id": "0c9e8d7b-1a2b-4c3d-9e8f-7a6b5c4d3e2f",
  "timestamp": "2026-11-05T12:00:00Z",
  "student_hash": "s_9f2c41ab",
  "lab_type": "cybersecurity",
  "module_id": "net-sec-03",
  "status": "completed",
  "minutes_spent": 45
}
```

`lab_type`: `ai`, `cybersecurity`, `networking`, `iot`. `status`: `started`, `in_progress`, `completed`.

## Output objects (backend -> frontend)

### `ticket`

```json
{
  "ticket_id": "T-0001",
  "created_at": "2026-11-05T10:16:05Z",
  "severity": "high",
  "location_id": "block-b",
  "affected_aps": ["ap-b-02"],
  "root_cause": "ap_hardware_failure",
  "explanation": "Only ap-b-02 shows 100% packet loss; neighbouring APs and the uplink are healthy.",
  "recommended_action": "Reboot or replace ap-b-02.",
  "status": "open"
}
```

`root_cause`: `ap_hardware_failure`, `isp_uplink_outage`, `congestion`, `iot_device_fault`, `unknown`.

### `advisory`

```json
{
  "advisory_id": "A-0001",
  "created_at": "2026-11-05T10:16:06Z",
  "message": "Block B Wi-Fi is degraded. Try Lab Network (12 seats free, stable Wi-Fi).",
  "affected_locations": ["block-b"],
  "suggested_location": "lab-network"
}
```

### `notification` (backend -> Telegram)

```json
{
  "notification_id": "N-0001",
  "created_at": "2026-11-05T10:16:07Z",
  "channel": "telegram",
  "ticket_id": "T-0001",
  "text": "[HIGH] Block B: ap-b-02 hardware failure. Action: reboot or replace ap-b-02.",
  "sent": false
}
```

`sent` becomes `true` after the Telegram sender delivers it. The dashboard shows this as "admin notified".

### `zone_status`

```json
{
  "location_id": "lab-network",
  "updated_at": "2026-11-05T10:16:10Z",
  "seats_total": 40,
  "seats_free": 12,
  "wifi_health": "good",
  "score": 0.86
}
```

`wifi_health`: `good`, `degraded`, `down`. `score`: 0 to 1, higher means a better place to be right now.

## Extra fields the backend returns

- `ticket`: also has `affected_devices` (IoT device ids), `resolved_at`, `resolution_note`. `status` is `open` or `resolved`. `location_id` is `campus` for an uplink outage.
- `advisory`: also has `kind` (`incident` or `recovery`) and `ticket_id`.
- `notification`: also has `error` (for example `telegram_not_configured`). `sent` is `false` until delivered.
- `zone_status`: also has `name` and `iot_devices_down`. `wifi_health` can be `unknown` when no probe has reported for that location yet.
- Events must **not** contain raw identifiers (`student_id`, `name`, `email`, ...). They are rejected with HTTP 422. Use `student_hash`, which looks like `s_` plus 8 to 64 hex characters.
- A flag trips after 3 bad readings in a row and clears after 3 good ones.
- `POST /events/batch` returns `accepted`, `duplicates`, `rejected`, `tickets_opened` and `tickets_resolved`. It classifies once after the whole batch is applied.
