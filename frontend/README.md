# frontend/ : Student Page & Staff Dashboard

**Owner: Pang Zai Yong**

Interactive web application for the **Smart Lab Companion** (APU Cloud Innovation Hackathon 2026).
Built with **React 19**, **TypeScript**, and **Vite**.

Provides two personas matching the project architecture:
1. **Student Companion (Raja)**: Real-time lab finder, dynamic seat counts, Wi-Fi health, live rerouting advisories, and the Lab Record learning advisor.
2. **Staff & IT Dashboard**: Campus-wide infrastructure health, autonomous incident feed with **Gemini root-cause intelligence**, one-click ticket resolution, and Telegram alert dispatch logs.
3. **Interactive Demo Controller**: 1-click fault simulator built into the UI for hackathon presentations and judges.

---

## Quick Start

```bash
# 1. Start the backend first (terminal 1, port 8000)
cd backend
source .venv/bin/activate       # Windows: .venv\Scripts\activate
uvicorn app.main:app --port 8000

# 2. Start the frontend (terminal 2)
cd frontend
npm install
npm run dev
```

Open your browser at **http://localhost:5173**.

> Backend CORS is preconfigured in `backend/app/main.py` to allow `http://localhost:5173` and `http://localhost:3000`.

---

## Key Features

### 1. Student Companion ("Raja's Journey")
Follows the student persona **Raja** through his daily campus lab experience:
* **Best Lab Right Now (`best_lab`)**: Prominent recommendation hero card showing the highest-scoring healthy lab with verified free seats and good Wi-Fi signal.
* **Real-time Incident Advisories**: Dynamic warning banners alerting students to network anomalies and automatically pointing them to alternative healthy labs.
* **Campus Facilities Directory**: Filterable cards covering all APU labs (AI, Cybersecurity, Networking, IoT) and academic zones (Block A, Block B, Library) with live occupancy gauges.
* **Raja's Lab Record (Roadmap / Phase 2 Preview)**: Tracks Raja's accumulated hands-on hours (IoT, AI, Networking) logged via backend `lab_activity` telemetry, with an intentional roadmap preview for the Phase 2 Gemini skill advisor.

### 2. Staff IT Operations Command Center
A professional monitoring dashboard for campus network and lab administrators:
* **Infrastructure KPIs**: Live metrics on monitored zones, campus-wide free seats, active incidents, and faulty IoT devices.
* **Autonomous Incident Feed (`open_tickets`)**: Real-time tickets raised by the backend detection engine with:
  * Autonomous classification (`ap_hardware_failure`, `isp_uplink_outage`, `congestion`, `iot_device_fault`).
  * **Gemini Root-Cause Explanation**: Natural language diagnosis of the failure mechanism.
  * **Recommended Operational Action**: Step-by-step IT remedy.
  * **One-Click Ticket Resolution**: Directly marks tickets as resolved (`POST /tickets/{id}/resolve`).
* **Zones Telemetry Matrix**: Tabular overview of seats, occupancy percentage, Wi-Fi status (cleanly showing *"No sensors"* for zones without probes like the Library), and composite health scores.
* **Telegram Admin Alert Stream (`recent_notifications`)**: Live feed of alert messages dispatched to the campus administrator Telegram bot.

### 3. Integrated Hackathon Demo Controller
A dedicated simulation toolbar hidden by default and activated via the **Demo Mode** button in the top navigation:
* **1. Kill AP (`ap-b-02`)**: Injects 3 bad readings into Block B &rarr; engine trips &rarr; ticket opened &rarr; Raja redirected to AI Lab.
* **2. Congest Block A**: Overloads Block A with 180+ clients &rarr; triggers congestion ticket.
* **3. Networking Lab Down**: Drops both APs in `lab-network`.
* **4. IoT Reader Fault**: Simulates card reader hardware failure.
* **5. Campus Uplink Outage**: Multi-location failure simulating total ISP outage.
* **6. Recover Health**: Sends 3 healthy readings &rarr; tickets auto-resolve.
* **7. Reset State**: Calls `POST /admin/reset` to restore a clean state.

---

## Backend Integration & Endpoints

The frontend integrates with Starlette/Uvicorn backend endpoints:

| Endpoint | Method | Frontend Usage |
|---|---|---|
| `/state` | `GET` | Polled automatically (default: every 2 seconds). Returns `zones`, `best_lab`, `open_tickets`, `active_advisories`, `recent_notifications`. |
| `/health` | `GET` | Liveness health check used by the connection status indicator and Settings test. |
| `/tickets/{id}/resolve` | `POST` | Dispatched when staff clicks **Mark Incident Resolved**. |
| `/admin/reset` | `POST` | Clears all backend state when starting a new demo run. |
| `/events/batch` | `POST` | Dispatched by the Demo Controller to inject simulated faults without requiring a separate terminal. |

### API Security & Configuration
- Set `VITE_API_BASE_URL` (default: `http://localhost:8000`) in `.env.local` if running against a custom or remote host.
- Set `VITE_DASHBOARD_API_KEY` if `DASHBOARD_API_KEY` is enabled in backend production mode.
- Users can also configure the backend URL, API keys, and polling frequency interactively through the **Settings Modal** (gear icon on the top right).

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── DemoController.tsx      # Hackathon presentation fault controller
│   │   ├── Navbar.tsx              # Top navigation, status indicator, persona tabs
│   │   ├── SettingsModal.tsx       # Backend URL & API key settings
│   │   ├── StaffDashboard.tsx      # IT command center & incident management
│   │   ├── StudentView.tsx         # Raja's lab companion & learning advisor
│   │   ├── TicketCard.tsx          # Ticket card with Gemini AI analysis & resolve
│   │   └── ZoneCard.tsx            # Lab & zone card with occupancy gauge
│   ├── context/
│   │   └── AppContext.tsx          # State management, auto-polling & actions
│   ├── services/
│   │   └── api.ts                  # HTTP client & telemetry simulation helpers
│   ├── types.ts                    # TypeScript types matching backend schema
│   ├── App.css                     # Modern APU dark-slate theme styles
│   ├── App.tsx                     # Main application shell
│   ├── index.css                   # Global resets & design tokens
│   └── main.tsx                    # React DOM entrypoint
├── index.html                      # HTML template with Google Fonts
├── package.json                    # Dependencies & scripts
├── tsconfig.json                   # TypeScript configuration
└── vite.config.ts                  # Vite config (port 5173, host: true)
```

---

## Build for Production

```bash
cd frontend
npm run build
npm run preview
```

The production assets are compiled to `frontend/dist/`.
