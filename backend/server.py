"""REST API Server & Static Asset Dispatcher.
Built using standard library http.server.ThreadingHTTPServer for zero-dependency reliability.
"""

import http.server
import json
import os
import posixpath
import sys
import time
import urllib.parse
from typing import Dict, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.config import SERVER_HOST, SERVER_PORT, AP_NODES, CAMPUS_GATEWAY, GEMINI_MODEL
from backend.storage import db
from backend.pipeline import pipeline
from backend.interpreter import interpreter
from backend.aiops_gemini import gemini_engine

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

class AIOpsRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP Request Handler supporting REST APIs and static file delivery."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json_response(self, data: Any, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def _send_text_response(self, text: str, content_type: str = "text/plain", filename: str = None):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # REST API Routes
        if path == "/api/status":
            self._handle_get_status()
        elif path == "/api/telemetry/history":
            self._handle_get_history()
        elif path == "/api/tickets":
            self._handle_get_tickets()
        elif path.startswith("/api/tickets/") and not path.endswith("/resolve"):
            ticket_id = path.replace("/api/tickets/", "").strip()
            self._handle_get_ticket_by_id(ticket_id)
        elif path == "/api/advisories":
            self._handle_get_advisories()
        elif path == "/api/pipeline/events":
            self._handle_get_pipeline_events(query)
        elif path == "/api/logs/live":
            self._handle_get_live_logs(query)
        elif path.startswith("/api/export/ticket/"):
            ticket_id = path.replace("/api/export/ticket/", "").strip()
            fmt = query.get("format", ["markdown"])[0]
            self._handle_export_ticket(ticket_id, fmt)
        elif path == "/api/config":
            self._handle_get_config()
        elif path == "/" or path == "/index.html":
            # Serve index.html
            self.path = "/index.html"
            super().do_GET()
        else:
            # Fallback to static files
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = {}
        if content_len > 0:
            raw_body = self.rfile.read(content_len).decode("utf-8")
            try:
                post_data = json.loads(raw_body)
            except Exception:
                post_data = {}

        if path == "/api/scenarios/inject":
            self._handle_post_scenario_inject(post_data)
        elif path.startswith("/api/tickets/") and path.endswith("/resolve"):
            parts = path.split("/")
            ticket_id = parts[3]
            self._handle_post_ticket_resolve(ticket_id)
        elif path == "/api/config/gemini-key":
            self._handle_post_gemini_key(post_data)
        elif path == "/api/logs/interpret":
            self._handle_post_log_interpret(post_data)
        else:
            self._send_json_response({"error": "Endpoint not found"}, 404)

    # Handlers
    def _handle_get_status(self):
        snapshot = db.get_latest_snapshot()
        scenario = db.get_scenario()
        advisories = db.get_advisories()
        open_tickets = [t for t in db.get_tickets() if t.get("status") == "OPEN"]
        
        resp = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pipeline": {
                "status": "RUNNING" if pipeline.is_running else "STOPPED",
                "state": pipeline.current_state,
                "agent": "Google Antigravity Real-Time Pipeline v2.0"
            },
            "active_scenario": scenario,
            "probes": snapshot,
            "open_tickets_count": len(open_tickets),
            "advisories": advisories,
            "gemini_engine": {
                "model": gemini_engine.active_model,
                "has_key": bool(db.get_gemini_key() or os.environ.get("GEMINI_API_KEY")),
                "last_status": gemini_engine.last_api_status,
                "last_error": gemini_engine.last_api_error
            }
        }
        self._send_json_response(resp)

    def _handle_get_history(self):
        history = db.get_telemetry_history()
        self._send_json_response(history)

    def _handle_get_tickets(self):
        tickets = db.get_tickets()
        self._send_json_response(tickets)

    def _handle_get_ticket_by_id(self, ticket_id: str):
        ticket = db.get_ticket(ticket_id)
        if ticket:
            self._send_json_response(ticket)
        else:
            self._send_json_response({"error": "Ticket not found"}, 404)

    def _handle_get_advisories(self):
        advisories = db.get_advisories()
        self._send_json_response(advisories)

    def _handle_get_pipeline_events(self, query):
        limit = int(query.get("limit", [40])[0])
        events = db.get_pipeline_events(limit=limit)
        self._send_json_response(events)

    def _handle_get_live_logs(self, query):
        limit = int(query.get("limit", [50])[0])
        severity = query.get("severity", [None])[0]
        ap_id = query.get("ap_id", [None])[0]
        logs = db.get_interpreted_logs(limit=limit, severity=severity, ap_id=ap_id)
        self._send_json_response(logs)

    def _handle_post_log_interpret(self, body: Dict[str, Any]):
        raw_log = body.get("log", "").strip()
        ap_id = body.get("ap_id", "MANUAL-INPUT")
        if not raw_log:
            self._send_json_response({"error": "Missing 'log' string in body"}, 400)
            return
        
        result = interpreter.interpret_log(raw_log, ap_id=ap_id)
        self._send_json_response(result)

    def _handle_get_config(self):
        resp = {
            "ap_nodes": AP_NODES,
            "gateway": CAMPUS_GATEWAY,
            "gemini_model": GEMINI_MODEL,
            "has_custom_key": bool(db.get_gemini_key())
        }
        self._send_json_response(resp)

    def _handle_post_scenario_inject(self, body: Dict[str, Any]):
        scenario_name = body.get("scenario", "NORMAL").upper()
        valid = ["NORMAL", "BLOCK_B_HARDWARE_FAILURE", "CAMPUS_ISP_OUTAGE", "LIBRARY_CONGESTION"]
        if scenario_name not in valid:
            self._send_json_response({"error": f"Invalid scenario. Allowed: {valid}"}, 400)
            return

        db.set_scenario(scenario_name)
        pipeline._emit_event(
            "SCENARIO_INJECTED",
            f"Judge/Operator injected scenario: [{scenario_name}]. Telemetry probes reacting immediately.",
            "ALERT"
        )
        self._send_json_response({
            "status": "OK",
            "scenario": scenario_name,
            "message": f"Scenario {scenario_name} activated successfully."
        })

    def _handle_post_ticket_resolve(self, ticket_id: str):
        resolved = db.resolve_ticket(ticket_id)
        if resolved:
            pipeline._emit_event(
                "TICKET_RESOLVED",
                f"IT Operator marked ticket #{ticket_id} as RESOLVED.",
                "SUCCESS"
            )
            self._send_json_response({"status": "OK", "ticket": resolved})
        else:
            self._send_json_response({"error": "Ticket not found"}, 404)

    def _handle_post_gemini_key(self, body: Dict[str, Any]):
        key = body.get("api_key", "").strip()
        if not key:
            db.set_gemini_key("")
            gemini_engine.last_api_status = "NOT_CONFIGURED"
            gemini_engine.last_api_error = ""
            self._send_json_response({
                "status": "OK",
                "message": "Gemini API key cleared. Reverted to Deterministic AIOps Engine.",
                "active": False
            })
            return

        # Perform active live validation against Google Cloud
        validation = gemini_engine.validate_key(key)
        if validation["valid"]:
            db.set_gemini_key(key)
            self._send_json_response({
                "status": "OK",
                "valid": True,
                "model": validation.get("model", "gemini-1.5-flash"),
                "message": validation.get("message", "API key verified successfully with Google Cloud!"),
                "active": True
            })
        else:
            # Key failed validation against Google Cloud!
            self._send_json_response({
                "status": "ERROR",
                "valid": False,
                "error_details": validation.get("error_details", ""),
                "message": validation.get("message", "Validation failed"),
                "active": False
            }, 400)

    def _handle_export_ticket(self, ticket_id: str, fmt: str):
        ticket = db.get_ticket(ticket_id)
        if not ticket:
            self._send_json_response({"error": "Ticket not found"}, 404)
            return

        if fmt == "json":
            self._send_text_response(
                json.dumps(ticket, indent=2),
                content_type="application/json",
                filename=f"{ticket_id}.json"
            )
        else:
            # Markdown format
            remediation_md = "\n".join([f"- [ ] {step}" for step in ticket.get("remediation_steps", [])])
            md = f"""# Enterprise IT Support Incident Ticket: {ticket.get('ticket_id')}

**Title**: {ticket.get('title')}
**Severity**: {ticket.get('severity')}
**Status**: {ticket.get('status')}
**Created At**: {ticket.get('created_at')}
**AIOps Engine**: {ticket.get('engine_mode', 'Google Cloud Gemini Enterprise')}
**AI Confidence Score**: {ticket.get('ai_confidence_pct')}%

---

## 1. Incident Overview & Blast Radius
- **Affected Nodes**: {", ".join(ticket.get('affected_nodes', []))}
- **Blast Radius**: {ticket.get('blast_radius')}

## 2. Root Cause Analysis (RCA)
{ticket.get('root_cause_explanation')}

## 3. Engineering Remediation Protocol
{remediation_md}

---
*Generated autonomously by Campus Wi-Fi Health AIOps (Google Antigravity + Gemini Enterprise)*
"""
            self._send_text_response(
                md,
                content_type="text/markdown",
                filename=f"{ticket_id}.md"
            )

def run_server(port: int = SERVER_PORT):
    """Starts the ThreadingHTTPServer and Antigravity Event Pipeline."""
    server_address = (SERVER_HOST, port)
    
    # Start the Antigravity background pipeline
    pipeline.start()
    
    httpd = http.server.ThreadingHTTPServer(server_address, AIOpsRequestHandler)
    print("=" * 70)
    print(" 🚀 CAMPUS WI-FI HEALTH - AUTONOMOUS AIOps PLATFORM")
    print("=" * 70)
    print(f" [Network Probes]     : Block A, Block B, Library Probes Active")
    print(f" [Antigravity Engine] : Real-time Event Pipeline Listening on Thread")
    print(f" [Gemini Enterprise]  : Multi-point Root Cause Analysis Ready")
    print(f" [Dashboard URL]      : http://localhost:{port}")
    print("=" * 70)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down gracefully...")
        pipeline.stop()
        httpd.server_close()
