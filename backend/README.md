# backend/

**Owner: Koguleswaraan**

Ingest API, storage, wiring, cloud config and security.

## Tasks
- [ ] GCP project, Cloud Run, Firestore (optional Pub/Sub)
- [ ] Ingest endpoint for simulator events
- [ ] Store events and compute `zone_status` (seats free plus Wi-Fi/IoT health) per lab and block
- [ ] Call the agent on threshold breaches and store `ticket`, `advisory` and `notification`
- [ ] Call the Telegram sender (`career/`) for each `notification`
- [ ] Expose endpoints for the frontend
- [ ] Security: secrets via env vars, dashboard auth, hashed student IDs
- [ ] End-to-end integration by 7 Nov
- [ ] Final submission as team leader

Suggested: Python + FastAPI. Config goes in `.env` (see `.env.example`).
