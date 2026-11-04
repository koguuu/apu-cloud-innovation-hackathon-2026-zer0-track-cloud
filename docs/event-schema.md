# Data contract (shared by everyone)

This is the one format everyone builds against so we can work in parallel.
**Change it only after telling the group.** All timestamps are ISO 8601 UTC.

## Locations

| `location_id` | Name | Capacity (seats) |
|---|---|---|
| `block-a` | Block A | 120 |
| `block-b` | Block B | 120 |
| `library` | Library | 200 |
| `lab-ai` | AI Lab | 40 |
| `lab-cyber` | Cybersecurity Lab | 40 |
| `lab-network` | Networking Lab | 40 |

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

### `lab_activity`

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

## Output objects (agent / backend -> frontend)

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

`root_cause`: `ap_hardware_failure`, `isp_uplink_outage`, `congestion`, `unknown`.

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

`wifi_health`: `good`, `degraded`, `down`. `score`: 0 to 1, higher means a better place to study.

### `career_suggestion`

```json
{
  "student_hash": "s_9f2c41ab",
  "generated_at": "2026-11-05T12:30:00Z",
  "hours_by_lab": { "ai": 5.0, "cybersecurity": 0.5, "networking": 2.0 },
  "top_matches": [
    { "role": "Cloud Infrastructure Engineer", "fit": 0.82 },
    { "role": "IoT Security Analyst", "fit": 0.74 }
  ],
  "recommended_certs": ["Google Cloud Associate Cloud Engineer", "CompTIA Network+"],
  "skills_to_gain": ["Linux", "Networking fundamentals", "IAM and cloud security"],
  "plan_6_months": [
    "Month 1-2: networking fundamentals and Linux",
    "Month 3-4: cloud basics and hands-on labs",
    "Month 5-6: certification prep and a portfolio project"
  ],
  "disclaimer": "This is a suggestion based on lab activity, not a final decision."
}
```
