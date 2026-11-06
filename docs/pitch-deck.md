# Smart Lab Companion — Pitch Deck

**APU Cloud Innovation Hackathon 2026**
Track: *Intelligent Automation & Digital Transformation*
Owner: Pang Zai Jie (everyone reviews). Export to PDF, max 10 MB.

---

## Slide 1 — Title

**Smart Lab Companion**

> *"From finding a working lab to knowing what to learn next — one companion for every student's lab journey."*

APU Cloud Innovation Hackathon 2026 · Intelligent Automation & Digital Transformation

Team: Htet Win · Raja · Pang Zai Yong · Pang Zai Jie · Koguleswaraan

---

## Slide 2 — The Problem (Raja's story)

**Labs are where skills are built. But right now:**

| Pain point | Reality today |
|---|---|
| "Which lab is free?" | No live view. Students walk from block to block. |
| "Is the Wi-Fi even working?" | IT finds out from student complaints, not from data. |
| "Where are my lab hours leading me?" | No personalised guidance at all. |

**The result:**
- Lost study time for students.
- Delayed IT response — faults fixed hours late.
- No feedback loop from lab activity to academic progress.

One student, **Raja**, wants to do his IoT lab assignment. He can't tell if the lab is free, working, or whether the AP is dead before he gets there.

---

## Slide 3 — Our Solution

### Smart Lab Companion

An **autonomous campus agent** that works in three layers:

```
Layer 1 — See          Wi-Fi & IoT health probes across every block and lab
Layer 2 — Think        Gemini finds the root cause; rules decide the action
Layer 3 — Act          IT ticket + student reroute + Telegram alert, instantly
```

**What Raja gets:**
- A live map of which labs are free and working, right now.
- An automatic redirect when his lab goes down.

**What IT gets:**
- An instant Telegram alert the moment a fault is detected.
- A categorised ticket with the root cause and the recommended fix — written by Gemini.

**Future (stretch):**
- A chatbot that turns Raja's own lab hours into "you should explore cybersecurity next."

---

## Slide 4 — Architecture

```
┌──────────────────┐          POST /events/batch         ┌────────────────────┐
│   Simulator      │  ──────────────────────────────────► │   Backend API      │
│  Wi-Fi · IoT     │                                      │   (Starlette)      │
│  Card events     │                                      └────────┬───────────┘
└──────────────────┘                                               │
                                                           ┌───────▼────────┐
                                                           │  engine.py     │
                                                           │  3-bad-reading │
                                                           │  trip rule     │
                                                           └───────┬────────┘
                                                                   │
                                                 ┌─────────────────▼──────────────────┐
                                                 │  Root-cause rules                   │
                                                 │  ap_hardware_failure                │
                                                 │  isp_uplink_outage (campus-wide)    │
                                                 │  congestion · iot_device_fault      │
                                                 └─────────────────┬──────────────────┘
                                                                   │
                                                 ┌─────────────────▼──────────────────┐
                                                 │  analyzer.py + Gemini              │
                                                 │  Writes plain-English explanation  │
                                                 │  Checks rule cause, corrects if    │
                                                 │  evidence clearly contradicts it   │
                                                 └──────────┬──────────┬─────────────┘
                                                            │          │
                                                 ┌──────────▼──┐  ┌───▼──────────────┐
                                                 │  IT Ticket  │  │  Student Advisory│
                                                 │  + Telegram │  │  "Try AI Lab     │
                                                 │  alert      │  │   (12 seats)"    │
                                                 └─────────────┘  └──────────────────┘
                                                            │
                                                 ┌──────────▼──────────────────────────┐
                                                 │  GET /state                          │
                                                 │  Student page + Staff dashboard      │
                                                 └─────────────────────────────────────┘
```

**Cloud stack:** Starlette backend → Cloud Run (1 instance, in-memory state) · Gemini Flash for explanations · Telegram Bot API for admin alerts. All data is simulated for the prototype.

---

## Slide 5 — Live Demo

### Demo story: one fault, four seconds

1. **Healthy campus.** The student page shows all labs with seats and green Wi-Fi.
2. **Inject a fault.** Type `kill-ap ap-b-02` in the simulator terminal. Block B's AP goes dead.
3. **Detection.** Three bad readings in a row (≈ 4 seconds at the default tick rate) trip the flag.
4. **Ticket + alert.** An IT ticket opens. The admin's Telegram gets:

```
🚨 [HIGH] Smart Lab Alert
📍 Location: Block B
🔎 Issue: 📡 AP Hardware Failure
🖥️ Affected: ap-b-02
🔧 Action: Reboot or replace ap-b-02; check its switch port and power.
📋 Ticket: T-0001
```

5. **Student reroute.** The advisory redirects Raja to the AI Lab (12 seats free, stable Wi-Fi).
6. **Auto-resolve.** Type `recover`. After 3 good readings, the ticket closes and a recovery advisory is posted.

---

## Slide 6 — AI at Work

### How Gemini does the analysis

**Rule engine (fast, deterministic):**
- Bad reading = latency ≥ 150 ms OR packet loss ≥ 5% OR RSSI ≤ −80 dBm.
- Flag trips after **3 bad readings in a row** (noise cannot trigger a false alert).
- Rules decide the root cause in milliseconds.

**Gemini (smart, explainable):**
- Receives the evidence JSON (AP metrics, healthy neighbours, device statuses).
- Returns a plain-English explanation + recommended action.
- Can correct `ap_hardware_failure` ↔ `congestion` when confident.
- Cannot override uplink or IoT causes (would break auto-resolve).

**Guard rails:**
- Gemini is **optional**. No key, quota hit, timeout or bad JSON → template text, no downtime.
- Alert and ticket go out **immediately** with template text; Gemini enriches in the background.
- Evidence is passed as data, not instructions. Output is length-capped and sanitised.
- One function (`app/llm.py: call_gemini`) → switching to Gemini Enterprise is a one-line change.

**Root causes:**

| Cause | Signal |
|---|---|
| `ap_hardware_failure` | One AP bad, neighbours healthy |
| `isp_uplink_outage` | ≥ 60% of APs bad across 2+ locations |
| `congestion` | High clients + high latency, low loss, good signal |
| `iot_device_fault` | Device reports `down`, Wi-Fi is fine |

---

## Slide 7 — Lab Record (stretch / roadmap)

### "What should I pursue next?" — a chatbot for every student

The backend already stores anonymised `lab_activity` events (hashed student ID, lab type, module, minutes spent, status). The chatbot is **not built yet**; this slide is the roadmap.

**How it would work:**

```
Student asks: "What should I study next?"
                        │
         ┌──────────────▼────────────────┐
         │  Retrieve lab_activity events  │
         │  for this student's hash      │
         └──────────────┬────────────────┘
                        │
         ┌──────────────▼────────────────┐
         │  Gemini prompt:               │
         │  "Given these lab hours and   │
         │   modules, suggest a next     │
         │   learning direction."        │
         └──────────────┬────────────────┘
                        │
         "You've spent 12 hours in the IoT lab
          and completed net-sec-03. Consider
          exploring cybersecurity next — the
          Cyber Lab is free right now."
```

**Privacy:** students are never identified by name. Every event uses `student_hash` (HMAC-SHA256 of the TP number, salted). Raw IDs are rejected at the API boundary (HTTP 422).

---

## Slide 8 — Impact, Privacy & Roadmap

### Impact

| Before | After |
|---|---|
| Students walk to labs and find them broken | Student page shows live Wi-Fi health and free seats |
| IT learns about faults from complaints, hours later | Telegram alert within **4 seconds** of a confirmed fault |
| No data on where lab hours lead | Lab Record chatbot turns hours into personalised guidance |

### Privacy & Security

- **Simulated data only.** Real deployment would use opt-in consent.
- Students identified only by `student_hash` (HMAC-SHA256, salted). Raw IDs rejected at the API.
- API keys protect every write and read endpoint (`X-API-Key`). Production refuses to start without them.
- Secrets (Gemini key, Telegram token) in `.env` only — never in Git.

### Roadmap to real APU data

```
Now (prototype)         Next sprint              Production
─────────────────       ─────────────────        ──────────────────
Simulated probes   →    Real AP SNMP/syslog  →   Firestore (multi-instance)
In-memory store    →    Cloud Firestore      →   Cloud Run autoscaling
Fake student IDs   →    Real TP hashes       →   Full privacy review + opt-in
Telegram only      →    Email + Slack        →   IT service-desk integration
```

### Submission checklist

- [ ] Deck exported as PDF, under 10 MB
- [ ] Demo tested 3 times end to end
- [ ] Demo video recorded as a backup
- [ ] Repo access checked with the organisers (private vs public)
- [ ] Summary is at least 50 characters
- [ ] HTTPS repository link added to submission form
- [ ] Demo link added (optional)
