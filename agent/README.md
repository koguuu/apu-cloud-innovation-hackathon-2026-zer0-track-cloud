# agent/

**Owner: Htet Win**

The AI brain: detects problems, finds the root cause with Gemini, writes tickets, advisories and notifications.

## Inputs
Recent `wifi_telemetry` and `iot_health` events (see [../docs/event-schema.md](../docs/event-schema.md)).

## Outputs
`ticket`, `advisory` and `notification` objects. The `notification` goes to Pang Zai Jie's Telegram sender (`career/`).

## Tasks
- [ ] Threshold checks (latency, packet loss, RSSI, device status)
- [ ] Gemini prompt for root cause: single AP failure vs uplink outage vs congestion vs IoT device fault
- [ ] Generate `ticket`, `advisory` and `notification` in the agreed format
- [ ] Keep prompts in separate files (easy to tune)

Rule of thumb for the prompt: one AP bad while neighbours are fine means hardware; many APs bad together means uplink.
