# backend/

**Owner: Koguleswaraan**

Ingest API, detection, tickets, advisories, lab status and security. Python, built on Starlette + uvicorn.
State is kept in memory (fine for the demo; one instance). Everything here runs locally with no cloud account.

## Run it

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest                                                  # 48 tests
uvicorn app.main:app --reload --port 8000
```

Check it: `curl http://localhost:8000/health`

Config comes from environment variables (see `../.env.example`). Everything is optional in dev. A `.env` file in `backend/` or the repo root is loaded automatically on start (real environment variables win; `.env` is git-ignored).

## What each teammate uses

| Who | What to do |
|---|---|
| **Raja** (simulator) | `POST /events` for each event (or `POST /events/batch` with a JSON array). Format: [`docs/event-schema.md`](../docs/event-schema.md). Use `POST /admin/reset` between demo runs. |
| **Pang Zai Yong** (frontend) | `GET /state` returns everything in one call: `zones`, `best_lab`, `open_tickets`, `active_advisories`, `recent_notifications`. CORS allows `localhost:5173` and `localhost:3000`. |
| **Htet Win** (agent) | The baseline is in `app/engine.py` (rules decide the root cause) and `app/analyzer.py` (Gemini writes the explanation, with a template fallback). Replace or improve either. All Gemini calls go through `app/llm.py: call_gemini()`, so switching to Gemini Enterprise is a one-function change. |
| **Pang Zai Jie** (Telegram) | Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` and alerts go out. Or plug in your own sender: `notifier.set_sender(fn)` where `fn(notification) -> bool`. |

## Endpoints

| Method and path | Key | What it does |
|---|---|---|
| `GET /health` | none | Liveness check |
| `POST /events` | ingest | One event. Returns `tickets_opened` / `tickets_resolved` |
| `POST /events/batch` | ingest | JSON array of events (max 500). Bad events are listed under `rejected`, good ones are still processed |
| `GET /state` | dashboard | Everything the frontend needs |
| `GET /zones`, `GET /zones/{id}` | dashboard | Seats free, Wi-Fi health, IoT devices down, score |
| `GET /tickets?status=open` | dashboard | Tickets, newest first |
| `GET /tickets/{id}`, `POST /tickets/{id}/resolve` | dashboard | One ticket, or mark it resolved by hand |
| `GET /advisories`, `GET /notifications` | dashboard | Latest 20, newest first |
| `POST /admin/reset` | ingest | Clear all state |

Quick demo with curl:

```bash
# three bad readings in a row trip the flag and open a ticket
for i in 1 2 3; do
  curl -s -X POST localhost:8000/events -H 'Content-Type: application/json' -d '{
    "event_type":"wifi_telemetry","event_id":"'$(uuidgen)'","timestamp":"2026-11-05T10:15:30Z",
    "location_id":"block-b","ap_id":"ap-b-02",
    "metrics":{"latency_ms":900,"packet_loss_pct":100,"rssi_dbm":-90,"clients":40}}'
done
curl -s localhost:8000/state
```

## How detection works

- A reading is **bad** if latency >= 150 ms, packet loss >= 5% or RSSI <= -80 dBm (all configurable).
- A flag **trips after 3 bad readings in a row** and **clears after 3 good ones**, so a single noisy reading never raises an alert.
- Root cause rules: many APs bad at once across 2+ locations means `isp_uplink_outage` (campus-wide, replaces per-AP tickets). Bad APs with many clients, low loss and good signal means `congestion`. Other bad APs mean `ap_hardware_failure`. An IoT device reporting `down` means `iot_device_fault`.
- Opening a ticket also creates a student advisory (pointing to the best healthy lab with free seats) and an admin notification. When readings recover, the ticket auto-resolves and a recovery advisory is posted.
- `seats_free` = capacity minus students currently inside (a student is in one place at a time).
- Gemini is optional. Without `GEMINI_API_KEY` the explanation comes from a template.

## Security and privacy

- **API keys:** `X-API-Key` header. `INGEST_API_KEY` protects writes, `DASHBOARD_API_KEY` protects reads. Unset = open (dev only). With `APP_ENV=production` the server **refuses to start** without both.
- The frontend has to send the dashboard key from the browser, so treat it as demo-level protection and not real user login.
- **No personal data:** events carrying raw identifiers (`student_id`, `email`, `name`, ...) are rejected with 422. Students are identified only by `student_hash`. `app/privacy.py: hash_student_id()` makes the hash (needs a secret `HASH_SALT`).
- Secrets only in environment variables. Logs never contain the Telegram token or Gemini key.

## Deploy (Cloud Run) when billing is sorted

```bash
cd backend
gcloud run deploy smart-lab-api --source . --region asia-southeast1 --allow-unauthenticated \
  --set-env-vars APP_ENV=production,INGEST_API_KEY=...,DASHBOARD_API_KEY=...,CORS_ORIGINS=https://your-frontend
```

State is in memory, so run **one instance** (`--max-instances 1`) and expect a reset on redeploy. Moving to Firestore later only touches `app/store.py`.

## Not done yet

- Real Gemini calls and real Telegram delivery are covered by tests with fakes only. They need a key and a bot token to try for real.
- Cloud Run deploy and Firestore: waiting on the billing / licence decision.
- Lab Record (stretch): `lab_activity` events are stored, but there is no chatbot yet.

## Batches

`POST /events/batch` classifies once, after the whole batch is applied, so a campus-wide outage becomes one ticket and one alert. Single `POST /events` classifies after each event, and severity is raised if more APs fail later.
