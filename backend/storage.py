"""Thread-safe In-Memory and Persistent Storage for Campus Wi-Fi Health AIOps.
Stores real-time telemetry buffers, Antigravity events, IT tickets, and student advisories.
"""

import threading
import time
from collections import deque
from typing import Dict, List, Any, Optional

class DataStore:
    def __init__(self):
        self._lock = threading.Lock()
        
        # Current active scenario
        self.active_scenario: str = "NORMAL"
        self.scenario_started_at: float = time.time()
        self.scenario_duration: int = 0 # 0 = indefinite until changed
        
        # Telemetry history: map from ap_id to deque of telemetry records
        self.telemetry_history: Dict[str, deque] = {
            "AP-A101": deque(maxlen=60),
            "AP-B204": deque(maxlen=60),
            "AP-LIB-G": deque(maxlen=60),
        }
        
        # Latest snapshot of all APs
        self.latest_snapshot: Dict[str, Any] = {}
        
        # Antigravity Pipeline Event Stream (last 100 events)
        self.pipeline_events: List[Dict[str, Any]] = []

        # Interpreted Live Logs Stream (last 120 logs with initial AI results)
        self.interpreted_logs: List[Dict[str, Any]] = []
        
        # IT Support Tickets (list of tickets, newest first)
        self.tickets: List[Dict[str, Any]] = []
        
        # Student Study Zone Advisories
        self.advisories: Dict[str, Any] = {
            "headline": "All Campus Wi-Fi Zones Operating Nominally",
            "status": "NORMAL",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "zones": {
                "Block A": {
                    "recommendation": "OPTIMAL",
                    "badge": "bg-emerald-500",
                    "quality_score": 98,
                    "avg_latency_ms": 16.2,
                    "status_text": "Superb connection quality. High bandwidth available.",
                    "best_for": "Zoom classes, large downloads & collaborative study."
                },
                "Block B": {
                    "recommendation": "OPTIMAL",
                    "badge": "bg-emerald-500",
                    "quality_score": 96,
                    "avg_latency_ms": 14.8,
                    "status_text": "Low latency, ideal for engineering tools and research.",
                    "best_for": "Lab projects, remote SSH sessions & coursework."
                },
                "Library": {
                    "recommendation": "OPTIMAL",
                    "badge": "bg-emerald-500",
                    "quality_score": 94,
                    "avg_latency_ms": 19.5,
                    "status_text": "Good connection with high capacity seating available.",
                    "best_for": "Quiet thesis writing & deep-focus research."
                }
            }
        }
        
        # Runtime Gemini Key override
        self.runtime_gemini_key: str = ""

    def set_scenario(self, scenario_name: str, duration: int = 0):
        with self._lock:
            self.active_scenario = scenario_name
            self.scenario_started_at = time.time()
            self.scenario_duration = duration

    def get_scenario(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name": self.active_scenario,
                "started_at": self.scenario_started_at,
                "duration": self.scenario_duration,
                "elapsed": round(time.time() - self.scenario_started_at, 1)
            }

    def record_telemetry(self, ap_id: str, record: Dict[str, Any]):
        with self._lock:
            if ap_id in self.telemetry_history:
                self.telemetry_history[ap_id].append(record)
            self.latest_snapshot[ap_id] = record

    def get_latest_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.latest_snapshot)

    def get_telemetry_history(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._lock:
            return {ap: list(records) for ap, records in self.telemetry_history.items()}

    def add_pipeline_event(self, event: Dict[str, Any]):
        with self._lock:
            self.pipeline_events.append(event)
            if len(self.pipeline_events) > 100:
                self.pipeline_events.pop(0)

    def get_pipeline_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self.pipeline_events[-limit:]))

    def add_interpreted_log(self, log_entry: Dict[str, Any]):
        with self._lock:
            self.interpreted_logs.append(log_entry)
            if len(self.interpreted_logs) > 120:
                self.interpreted_logs.pop(0)

    def get_interpreted_logs(self, limit: int = 60, severity: str = None, ap_id: str = None) -> List[Dict[str, Any]]:
        with self._lock:
            filtered = self.interpreted_logs
            if severity and severity != "ALL":
                filtered = [l for l in filtered if l.get("severity") == severity]
            if ap_id and ap_id != "ALL":
                filtered = [l for l in filtered if l.get("ap_id") == ap_id]
            return list(reversed(filtered[-limit:]))

    def add_ticket(self, ticket: Dict[str, Any]):
        with self._lock:
            # Check if an open ticket for the same root cause already exists
            for existing in self.tickets:
                if existing.get("status") == "OPEN" and existing.get("root_cause_category") == ticket.get("root_cause_category") and existing.get("affected_zone") == ticket.get("affected_zone"):
                    # Update timestamp and evidence instead of duplicating
                    existing["last_updated"] = ticket.get("created_at")
                    existing["occurrences"] = existing.get("occurrences", 1) + 1
                    existing["latest_telemetry"] = ticket.get("latest_telemetry")
                    return existing
            
            # Prepend new ticket
            self.tickets.insert(0, ticket)
            if len(self.tickets) > 50:
                self.tickets.pop()
            return ticket

    def resolve_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self.tickets:
                if t.get("ticket_id") == ticket_id:
                    t["status"] = "RESOLVED"
                    t["resolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    return t
            return None

    def get_tickets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.tickets)

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for t in self.tickets:
                if t.get("ticket_id") == ticket_id:
                    return dict(t)
            return None

    def update_advisories(self, advisory_data: Dict[str, Any]):
        with self._lock:
            self.advisories = advisory_data

    def get_advisories(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.advisories)

    def set_gemini_key(self, key: str):
        with self._lock:
            self.runtime_gemini_key = key.strip()

    def get_gemini_key(self) -> str:
        with self._lock:
            return self.runtime_gemini_key

# Global singleton
db = DataStore()
