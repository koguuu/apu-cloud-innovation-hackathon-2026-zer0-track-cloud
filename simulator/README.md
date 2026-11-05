# simulator/

**Owner: Raja**

Generates all simulated data and injects faults for the demo.

## Outputs (see [../docs/event-schema.md](../docs/event-schema.md))
- `wifi_telemetry` for Block A, Block B and the labs (AI, Cyber, Network, IoT)
- `iot_health` (device status per location)
- `card_access` (enter/exit) for the labs
- *(Stretch)* `lab_activity` (hours and modules per anonymised student)

## Tasks
- [x] Wi-Fi probes with realistic noise and a normal daily pattern
- [x] IoT device health events
- [x] Card-reader log generator (occupancy rises and falls)
- [x] Fault injection: kill an AP, degrade a block, take a lab network down, uplink outage (plus congestion and an IoT fault)
- [x] One command to run everything for the demo
- [ ] *(Stretch)* Lab activity generator

Written for Python 3.9 or newer (tested on 3.13). Standard library only, so there is nothing to install to run it.

## Run it

Start the backend first (see [../backend/README.md](../backend/README.md)), then from the repo root:

```bash
python simulator/run.py              # normal campus, type fault commands while it runs
python simulator/run.py --demo       # same, plus a scripted fault timeline (about 3 minutes)
python simulator/run.py --dry-run    # print one tick of events as JSON, no backend needed
```

It clears the backend at start (`POST /admin/reset`; skip with `--no-reset`), then sends one batch to `POST /events/batch` every tick (2 seconds).
Config is optional: see [.env.example](.env.example). The backend URL comes from `BACKEND_URL` (default `http://localhost:8000`) and the key from `INGEST_API_KEY`.

Options: `--url`, `--tick SECONDS`, `--seed N`, `--demo`, `--no-reset`, `--no-interactive`, `--ticks N`, `--dry-run`.

## Fault commands (type them while it runs)

| Command | What it does | Expected ticket |
|---|---|---|
| `kill-ap [ap-id]` (default `ap-b-02`) | One AP dies | `ap_hardware_failure` |
| `degrade-block [block]` (default `block-b`) | Every AP in a block degrades | `ap_hardware_failure` |
| `lab-down [lab]` (default `lab-network`) | Every AP in a lab dies | `ap_hardware_failure` |
| `congestion [block]` (default `block-a`) | A block is overloaded (150+ clients per AP) | `congestion` |
| `iot-fault [device-id]` (default `reader-net-01`) | An IoT device reports `down` | `iot_device_fault` |
| `uplink` | Every AP dies | `isp_uplink_outage` (campus-wide) |
| `recover [target]` | Fix everything, or one AP / device / location | tickets auto-resolve |
| `reset`, `status`, `help`, `quit` | | |

A fault is detected after 3 bad readings in a row, so with the default 2-second tick the ticket appears about 4 seconds after the command.
Tickets resolve after 3 good readings, so keep the simulator running after `recover`.

## What it simulates

- **Layout:** 3 APs in each block, 2 in each lab (14 in total), unique ids (`ap-a-01`, `ap-ai-01`, ...). 7 IoT devices (4 card readers, 1 sensor, 2 switches).
- **Day pattern:** one simulated day (07:00 to 21:00) lasts 240 real seconds, with peaks at 10:30 and 15:00. Block clients per AP peak near 85, labs fill to at most 90% so there is always a free seat.
- **Noise:** normal readings stay inside latency < 110 ms, loss < 2.5%, RSSI > -72 dBm. An AP occasionally blips (one bad reading) but never twice in a row, so noise alone cannot open a ticket.
- **Card events:** 220 fake students with ids like `s_9f2c41ab12`. Labs fill and empty with the day pattern and never exceed 40.
- **IoT:** healthy devices report every 3rd tick, faulty ones every tick.

## Known behaviour of the backend (not the simulator)

- **Uplink outage sends extra alerts first.** The backend classifies each AP as soon as it trips, so before the campus-wide ticket exists it opens up to 3 per-location tickets (and 3 Telegram alerts), then supersedes them. Fix idea for the backend: classify once at the end of each batch, or wait a moment before opening tickets.
- **Severity stays `medium` for degrade-block and lab-down.** Severity is set when the first AP trips, when the rest of the location still looks healthy.

## Tests

```bash
pip install -r backend/requirements-dev.txt
python -m pytest simulator -q
```

The contract test validates every generated event with the backend's own models.
