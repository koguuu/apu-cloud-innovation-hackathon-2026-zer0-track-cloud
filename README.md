# Campus Wi-Fi Health: Autonomous AIOps & Student Study Zone Adviser

> **An autonomous AIOps monitoring and root-cause analysis platform that continuously tracks simulated campus Wi-Fi telemetry, detects degradation and hardware failures, automatically logs enterprise IT support tickets, and dynamically routes students to optimal study zones.**

---

## 🏆 Why This Idea Wins
* **Zero Physical Hardware**: 100% software simulated IoT probes. No hardware breadboards, wiring, or physical sensors required.
* **Deep Convergence**: Demonstrates a real closed loop connecting **IoT Probes + Google Antigravity + Gemini Enterprise Cloud**.
* **Explainable AI (XAI) Interpretability**: Real-time micro-inference on every incoming syslog line with root-cause reasoning, confidence ratings, and feature signal weights.
* **High-Impact Enterprise AIOps**: Moves past generic chatbot wrappers by delivering an authentic, high-impact Network Operations Center (NOC) and student utility.

---

## 🏗️ Architecture & Technology Convergence

```
   ┌─────────────────────────────────────────────────────────────┐
   │                     1. IoT & Network Layer                  │
   │  Simulated Access Point Probes (Block A, Block B, Library)  │
   │   - Latency (ms), Packet Loss (%), RSSI (dBm), Syslogs      │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ Continuous Telemetry (1.5s)
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                 2. Google Antigravity Pipeline              │
   │   - Background Autonomous Monitoring Daemon                 │
   │   - Multi-Point Threshold & Anomaly Detection               │
   │   - Event Packaging & Real-Time Cloud Stream                │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ Incident Event Dispatch
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │             3. Gemini Enterprise Cloud (Google Cloud)       │
   │   - Multi-Point Telemetry & Syslog Correlation              │
   │   - Root Cause Analysis (AP Crash vs ISP Flap vs Congestion)│
   │   - Automated IT Support Ticket Generation                  │
   │   - Dynamic Student Study Zone Advisory Routing             │
   └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Live Demo Scenarios (Judge Control Center)

The dashboard includes a **One-Click Scenario Injector** built directly into the UI:

| Scenario | Simulated Symptoms | Antigravity Action | Gemini Root Cause & Outcome |
| :--- | :--- | :--- | :--- |
| **🟢 Nominal Baseline** | Latency < 20ms, Loss 0%, RSSI -58 dBm across all blocks. | Emits heartbeat SLA compliance. | System nominal. All study zones marked **OPTIMAL** (98% quality). |
| **🔴 Block B Hardware Crash** | AP-B204 drops to 100% loss, 999ms latency; PCIe kernel panic syslogs. Block A and Library stay healthy. | Detects critical breach on AP-B204; packages incident event. | **Root Cause**: Isolated PCIe radio transceiver failure. Generates P2 IT ticket with PoE bounce / technician dispatch steps. Advises students to vacate Block B for Block A. |
| **🟡 Campus ISP Flap** | All APs (Block A, Block B, Library) experience 380ms+ latency & 30% loss to DNS 8.8.8.8, but internal LAN ping is normal. | Detects simultaneous multi-point anomaly across all probes. | **Root Cause**: Upstream ISP fiber degradation. Generates campus-wide P1 ticket. Advises students that external cloud exams are affected. |
| **🟠 Library Overcrowding** | Library clients surge to 290+ (capacity 220), channel utilization hits 98%, latency rises to 90ms. | Detects RF saturation and airtime duty cycle breach. | **Root Cause**: Localized co-channel interference & overcapacity. Generates P3 optimization ticket. Routes students to Block A concourse. |

---

## 🧠 Explainable AI (XAI) & Live Log Interpretability

Unlike "black-box" monitoring systems, every single raw syslog emitted by simulated APs is accompanied by an **Initial AI Result**:
1. **AI Classification**: Tags the operational domain (e.g. `HARDWARE_DRIVER_FAULT`, `WAN_UPLINK_DEGRADATION`, `RF_AIRTIME_SATURATION`, `NOMINAL_OPERATIONS`).
2. **Plain-English Interpretability Reasoning**: Explains *why* the AI concluded this root cause (e.g., explaining why a PCIe AER error points to a physical hardware crash instead of RF congestion).
3. **Feature Importance & Signal Weights**: Shows contributing factors (e.g. `hardware_aer_error: 95%`, `packet_loss: 98%`, `rf_contention: 1%`).
4. **Interactive Sandbox**: Use the **Test Custom Log** modal to type or paste any arbitrary syslog message and inspect the real-time AI classification on demand.

---

## ⚡ Quickstart

### Prerequisites
* Python 3.8+ (Zero external pip dependencies required — uses Python Standard Library!)

### Running the Application
Double-click `run.bat` or run:

```bash
# In PowerShell / Command Prompt
python start.py --port 8080
```

Open your browser to:
```
http://localhost:8080
```

---

## 🔑 Hybrid Gemini Integration
The prototype runs out of the box in **Hybrid Mode**:
1. **Live Gemini 2.5 Flash**: If `GEMINI_API_KEY` is set in the environment or entered via the **API Settings** button in the dashboard, calls are made directly to the Google Generative Language API.
2. **Deterministic High-Fidelity AIOps Fallback**: If offline or no key is provided, the embedded AIOps engine produces identical enterprise-grade root-cause analyses, ensuring a flawless presentation to judges without API quota or network hurdles.

---

## 📁 Repository Structure
```
├── backend/
│   ├── config.py         # Network topology, AP metadata, thresholds
│   ├── storage.py        # In-memory thread-safe event, ticket, & telemetry store
│   ├── probes.py         # Simulated IoT Probes (Block A, Block B, Library)
│   ├── pipeline.py       # Google Antigravity Background Event Pipeline
│   ├── aiops_gemini.py   # Gemini Enterprise Cloud RCA Engine (Live + Fallback)
│   └── server.py         # High-performance ThreadingHTTPServer & REST API
├── static/
│   ├── index.html        # Modern NOC Dashboard & Student Study Zone UI
│   ├── css/custom.css    # Radar pulse animations, terminal styling
│   └── js/app.js         # Real-time state management, Chart.js feeds, scenario actions
├── test_pipeline.py      # Automated verification test suite
├── start.py              # Master application runner
├── run.bat               # Windows batch launcher
├── run.ps1               # PowerShell launcher
└── README.md             # Project documentation
```

---

## 🧪 Running the Automated Verification Tests
```bash
python test_pipeline.py
```
Outputs validation across all 5 key pipeline stages:
1. Normal probe polling
2. Anomaly scenario injection
3. Antigravity threshold breach detection
4. Gemini Root Cause Analysis generation
5. ISP vs Local AP differential correlation
