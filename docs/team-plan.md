# Team plan

Deadline: **10 Nov 2026, 11:59 PM MYT** (aim to submit in the afternoon).
Feature freeze: **8 Nov**. Registration closes **8 Nov, 11:59 PM**.

## Roles and tasks

### Htet Win: AI agent (`agent/`)
- [ ] Threshold checks on incoming telemetry (latency, packet loss, RSSI)
- [ ] Gemini prompt: root-cause analysis (single AP failure vs uplink outage vs congestion)
- [ ] Generate `ticket` and `advisory` objects (see data contract)
- [ ] Keep prompts in files so they are easy to tune

### Raja: simulators (`simulator/`)
- [ ] Wi-Fi probe script for Block A, Block B and Library (realistic noise, normal day pattern)
- [ ] Card-reader log generator (enter/exit, occupancy rises and falls through the day)
- [ ] Lab activity generator (hours and modules per student per lab type)
- [ ] Fault injection command: kill an AP, degrade a block, simulate uplink outage
- [ ] One command to run the whole simulation for the demo

### Pang Zai Yong: frontend (`frontend/`)
- [ ] Student page: ranked zones, seats free, Wi-Fi health, advisory banner
- [ ] Staff dashboard: live alerts, ticket list, simple trend chart
- [ ] Career panel (with opt-in notice), fed by Pang Zai Jie's output
- [ ] Demo-ready look (clean, readable on a projector)

### Pang Zai Jie: career path + pitch (`career/`, `docs/pitch-outline.md`)
- [ ] Aggregate lab hours and modules per anonymised student
- [ ] Role and certificate mapping (SOC Analyst, Cloud Infrastructure, IoT Security, etc.)
- [ ] Gemini prompt that returns a `career_suggestion` (see data contract)
- [ ] Own the pitch deck story (PDF, max 10 MB) and demo script

### Koguleswaraan: cloud, backend, security (`backend/`)
- [ ] GCP project, Cloud Run, Firestore, optional Pub/Sub, environment config
- [ ] Ingest API and storage, endpoints for the frontend
- [ ] Wire simulator -> backend -> agent -> frontend end to end
- [ ] Security: secrets handling, auth for the dashboard, hashed student IDs
- [ ] Repo hygiene, PR reviews, final submission (as team leader)

## Timeline

| Date | Goal |
|---|---|
| 4 Nov (tonight) | Lock idea and roles, agree data contract, repo scaffold |
| 5-6 Nov | Everyone builds their own part against the data contract |
| 7 Nov | Connect everything, first end-to-end run |
| 8 Nov | Career module done, **feature freeze**, **team registration closes 11:59 PM** |
| 9 Nov | Polish, pitch deck, record demo video, run the demo 3 times |
| 10 Nov | Submit by the afternoon (leader submits: title, track, summary, repo link, PDF deck) |

## Definition of done (for the demo)

- Fault injection triggers a ticket and an advisory within about 10 seconds
- Student page reroutes to a healthy zone after the fault
- Career suggestion appears for a sample student
- Whole demo runs from one command plus one browser tab
- No secrets in the repo

## Risks

- **Scope:** two outputs in 6 days. Core demo (Wi-Fi + study zone) comes first, career is a Gemini module on the same logs and stays simple.
- **Integration:** most bugs show up when connecting parts. Do the first end-to-end run by 7 Nov.
- **Judging criteria not yet published:** check Discord and adjust the pitch.
