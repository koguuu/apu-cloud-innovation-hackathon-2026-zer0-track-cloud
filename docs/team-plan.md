# Team plan

Deadline: **10 Nov 2026, 11:59 PM MYT** (aim to submit in the afternoon).
Team registration closes **8 Nov, 11:59 PM**.

## Scope

- **Core (build first): Campus Health.** Wi-Fi and IoT health for Block A, Block B and the labs, root-cause analysis, auto ticket, Telegram alert to the admin, and a student page showing which labs are free and working.
- **Stretch: Lab Record.** Lab hours and modules, plus a Gemini chatbot: "what should I pursue next?"
- **Checkpoint: 7 Nov.** After the first end-to-end run, if the chatbot isn't working, it becomes a roadmap slide in the pitch and not a feature.

## Roles and tasks

### Htet Win: AI agent (`agent/`) [core]
- [ ] Threshold checks on telemetry (latency, packet loss, RSSI) and IoT health
- [ ] Gemini prompt for root cause: single AP failure vs uplink outage vs congestion vs IoT device fault
- [ ] Generate `ticket` and `advisory` objects (see data contract)
- [ ] When a ticket is created, produce a `notification` and hand it to Pang Zai Jie's Telegram sender
- [ ] Keep prompts in files so they are easy to tune

### Raja: simulators (`simulator/`) [core]
- [ ] Wi-Fi probes for Block A, Block B and the labs (AI, Cyber, Network, IoT), with realistic noise and a normal day pattern
- [ ] IoT device health events (`iot_health`)
- [ ] Card-reader log generator (enter/exit, occupancy rises and falls)
- [ ] Fault injection: kill an AP, degrade a block, take a lab network down, uplink outage
- [ ] One command to run the whole simulation for the demo
- [ ] *(Stretch)* Lab activity generator (hours and modules per student)

### Pang Zai Yong: frontend (`frontend/`) [core]
- [ ] Mock data first (use the examples in the data contract) so you are not blocked
- [ ] Student page: labs and blocks with seats free, Wi-Fi/IoT health, "best lab right now", advisory banner
- [ ] Staff dashboard: live alerts, ticket list, and a "admin notified on Telegram" status
- [ ] Demo-ready look (clean, readable on a projector)
- [ ] Switch from mock data to backend endpoints by 7 Nov
- [ ] *(Stretch)* Chatbot panel for Lab Record

### Pang Zai Jie: Telegram alert, occupancy, pitch (`career/`) [core + stretch]
- [ ] Create the Telegram bot (BotFather), store the token in `.env`
- [ ] `send_alert(notification)` function: short message with location, root cause and recommended action
- [ ] Occupancy: turn card-reader events into `seats_free` per lab
- [ ] Pitch deck story (PDF, max 10 MB) and demo script (`docs/pitch-outline.md`)
- [ ] *(Stretch, after the 7 Nov checkpoint)* Lab Record: aggregate lab hours, Gemini chatbot "what should I pursue next?", outage flag rule

### Koguleswaraan: cloud, backend, security (`backend/`) [core]
- [ ] GCP project, Cloud Run, Firestore, optional Pub/Sub, environment config
- [ ] Ingest API and storage, endpoints for the frontend
- [ ] Compute `zone_status` (seats free plus Wi-Fi/IoT health) for each lab and block
- [ ] Wire simulator -> backend -> agent -> Telegram -> frontend end to end by 7 Nov
- [ ] Security: secrets handling, auth for the dashboard, hashed student IDs
- [ ] Repo hygiene, PR reviews, final submission (as team leader)

## Timeline

| Date | Goal |
|---|---|
| 4-5 Nov | Lock scope and roles, everyone reads the data contract, backend hello-world deployed |
| 5-6 Nov | Everyone builds their own part against the data contract |
| **7 Nov** | First end-to-end run. **Checkpoint:** decide whether Lab Record stays in |
| 8 Nov | Feature freeze. **Team registration closes 11:59 PM** |
| 9 Nov | Polish, pitch deck, record demo video, run the demo 3 times |
| 10 Nov | Submit by the afternoon (leader submits: title, track, summary, repo link, PDF deck) |

## Definition of done (for the demo)

- Fault injection triggers a ticket, an advisory and a Telegram alert within about 10 seconds
- Student page sends the student to a healthy lab after the fault
- Whole demo runs from one command plus one browser tab
- No secrets in the repo
- *(Stretch)* Chatbot answers "what should I pursue next?" from a sample student's lab hours

## Risks

- **Blurred pitch:** Campus Health is the story. Lab Record is a short extra, and is cut if it isn't ready.
- **Integration:** most bugs show up when connecting parts. First end-to-end run by 7 Nov.
- **Judging criteria not yet published:** check Discord and adjust the pitch.
