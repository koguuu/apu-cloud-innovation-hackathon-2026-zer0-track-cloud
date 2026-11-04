# simulator/

**Owner: Raja**

Generates all simulated data and injects faults for the demo.

## Outputs (see [../docs/event-schema.md](../docs/event-schema.md))
- `wifi_telemetry` for Block A, Block B and the labs (AI, Cyber, Network, IoT)
- `iot_health` (device status per location)
- `card_access` (enter/exit) for the labs
- *(Stretch)* `lab_activity` (hours and modules per anonymised student)

## Tasks
- [ ] Wi-Fi probes with realistic noise and a normal daily pattern
- [ ] IoT device health events
- [ ] Card-reader log generator (occupancy rises and falls)
- [ ] Fault injection: kill an AP, degrade a block, take a lab network down, uplink outage
- [ ] One command to run everything for the demo
- [ ] *(Stretch)* Lab activity generator

Suggested: Python. Send events to the backend ingest endpoint (URL in `.env`).
