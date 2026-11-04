# agent/

**Owner: Htet Win**

The AI brain: detects problems, finds the root cause with Gemini, writes tickets and advisories.

## Inputs
Recent `wifi_telemetry` events (see [../docs/event-schema.md](../docs/event-schema.md)).

## Outputs
`ticket` and `advisory` objects.

## Tasks
- [ ] Threshold checks (latency, packet loss, RSSI)
- [ ] Gemini prompt for root cause: single AP failure vs uplink outage vs congestion
- [ ] Generate `ticket` and `advisory` in the agreed format
- [ ] Keep prompts in separate files (easy to tune)

Rule of thumb for the prompt: one AP bad while neighbours are fine means hardware; many APs bad together means uplink.
