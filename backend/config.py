"""Configuration for Campus Wi-Fi Health AIOps Platform.
Defines network topology, telemetry thresholds, and cloud integration settings.
"""

import os

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.environ.get("PORT", "8080"))

# Access Point (AP) Nodes & Campus Locations
AP_NODES = {
    "AP-A101": {
        "id": "AP-A101",
        "name": "Block A - Main Hall",
        "zone": "Block A (Lecture Halls & Classrooms)",
        "model": "Cisco Catalyst 9130AX",
        "ip": "10.14.10.11",
        "mac": "00:26:86:F1:A1:01",
        "channel_2g": 1,
        "channel_5g": 36,
        "nominal_clients": 45,
        "max_capacity": 150,
        "study_suitability": "Optimal for collaborative study and lecture note syncing."
    },
    "AP-B204": {
        "id": "AP-B204",
        "name": "Block B - Engineering Lab",
        "zone": "Block B (Computer Labs & Admin)",
        "model": "Aruba AP-555 Wi-Fi 6",
        "ip": "10.14.20.24",
        "mac": "28:6F:7F:C2:B2:04",
        "channel_2g": 6,
        "channel_5g": 48,
        "nominal_clients": 30,
        "max_capacity": 120,
        "study_suitability": "Ideal for lab workstations and compute-heavy projects."
    },
    "AP-LIB-G": {
        "id": "AP-LIB-G",
        "name": "Library - Quiet Reading",
        "zone": "Library (Ground & Mezzanine Floors)",
        "model": "Meraki MR56 High Density",
        "ip": "10.14.30.15",
        "mac": "E0:55:3D:88:C3:09",
        "channel_2g": 11,
        "channel_5g": 149,
        "nominal_clients": 110,
        "max_capacity": 220,
        "study_suitability": "Best for quiet deep-focus study and thesis writing."
    }
}

# Network Core & Gateway
CAMPUS_GATEWAY = {
    "ip": "10.14.0.1",
    "isp": "National Research & Education Network (NREN) Fiber 10Gbps",
    "dns_check": "8.8.8.8"
}

# Telemetry Anomaly Detection Thresholds (Antigravity Pipeline)
THRESHOLDS = {
    "latency_warning_ms": 45.0,
    "latency_critical_ms": 140.0,
    "packet_loss_warning_pct": 3.0,
    "packet_loss_critical_pct": 12.0,
    "rssi_degraded_dbm": -75.0,
    "rssi_critical_dbm": -85.0,
    "congestion_client_ratio": 0.85, # 85% of max capacity
    "cooldown_seconds": 15           # cooldown between identical incident alerts
}

# Gemini Enterprise Cloud AIOps Settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_FALLBACK_MODELS = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
