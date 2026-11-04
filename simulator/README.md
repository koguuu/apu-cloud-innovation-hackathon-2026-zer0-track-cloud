# simulator/

**Owner: Raja**

Generates all simulated data and injects faults for the demo.

## Outputs (see [../docs/event-schema.md](../docs/event-schema.md))
- `wifi_telemetry` for Block A, Block B and Library
- `card_access` (enter/exit) for labs and the library
- `lab_activity` (hours and modules per anonymised student)

## Tasks
- [ ] Wi-Fi probes with realistic noise and a normal daily pattern
- [ ] Card-reader log generator (occupancy rises and falls)
- [ ] Lab activity generator
- [ ] Fault injection: kill an AP, degrade a block, uplink outage
- [ ] One command to run everything for the demo

Suggested: Python. Send events to the backend ingest endpoint (URL in `.env`).
