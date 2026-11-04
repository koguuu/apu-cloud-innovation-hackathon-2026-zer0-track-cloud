# backend/

**Owner: Koguleswaraan**

Ingest API, storage, wiring, cloud config and security.

## Tasks
- [ ] GCP project, Cloud Run, Firestore (optional Pub/Sub)
- [ ] Ingest endpoint for simulator events
- [ ] Store events, compute `zone_status`, expose endpoints for the frontend
- [ ] Call the agent on threshold breaches and store `ticket` and `advisory`
- [ ] Security: secrets via env vars, dashboard auth, hashed student IDs
- [ ] End-to-end integration by 7 Nov
- [ ] Final submission as team leader

Suggested: Python + FastAPI. Config goes in `.env` (see `.env.example`).
