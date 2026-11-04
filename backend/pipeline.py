"""Google Antigravity Real-Time Event Pipeline.
Continuously runs as a background autonomous monitoring agent that ingests
telemetry from simulated IoT probes, detects threshold anomalies, packages multi-point
incident events, and dispatches them to Gemini Enterprise Cloud for Root Cause Analysis.
"""

import random
import threading
import time
import uuid
from typing import Dict, Any, List
from backend.config import THRESHOLDS, AP_NODES
from backend.storage import db
from backend.probes import probes
from backend.aiops_gemini import gemini_engine

class AntigravityEventPipeline:
    def __init__(self):
        self.is_running = False
        self._thread: threading.Thread = None
        self.last_incident_signature: str = ""
        self.last_incident_time: float = 0.0
        self.current_state: str = "HEALTHY" # "HEALTHY", "ANOMALY_ACTIVE", "RECOVERING"

    def start(self):
        """Starts the background Antigravity pipeline thread."""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="AntigravityPipelineWorker")
            self._thread.start()
            self._emit_event(
                "PIPELINE_INIT",
                "Google Antigravity Real-Time Event Pipeline initialized and listening for probe telemetry.",
                "INFO"
            )

    def stop(self):
        self.is_running = False

    def _worker_loop(self):
        """Continuous background autonomous loop."""
        while self.is_running:
            try:
                # 1. Sample telemetry from all probes
                snapshot = probes.poll_all_probes()
                
                # 2. Evaluate thresholds and detect anomalies
                anomalies = self._evaluate_anomalies(snapshot)
                
                if anomalies:
                    self._handle_anomaly_detected(snapshot, anomalies)
                else:
                    self._handle_healthy_state(snapshot)
                    
            except Exception as e:
                self._emit_event(
                    "PIPELINE_EXCEPTION",
                    f"Pipeline processing error: {str(e)}",
                    "ERROR"
                )
            
            # Tick interval: 1.5 seconds for snappy real-time UI updates
            time.sleep(1.5)

    def _evaluate_anomalies(self, snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scans current telemetry snapshot for threshold breaches."""
        detected = []
        
        for ap_id, data in snapshot.items():
            lat = data.get("latency_ms", 0)
            loss = data.get("packet_loss_pct", 0)
            rssi = data.get("rssi_dbm", -60)
            clients = data.get("connected_clients", 0)
            max_cap = data.get("max_capacity", 150)
            
            # Anomaly rules
            if loss >= THRESHOLDS["packet_loss_critical_pct"] or lat >= THRESHOLDS["latency_critical_ms"]:
                detected.append({
                    "ap_id": ap_id,
                    "type": "CRITICAL_SLA_BREACH",
                    "reason": f"Packet loss ({loss}%) or latency ({lat}ms) breached critical threshold.",
                    "severity": "CRITICAL",
                    "metrics": {"loss": loss, "latency": lat, "rssi": rssi}
                })
            elif clients > (max_cap * THRESHOLDS["congestion_client_ratio"]):
                detected.append({
                    "ap_id": ap_id,
                    "type": "CONGESTION_SATURATION",
                    "reason": f"Client density ({clients}/{max_cap}) reached saturation capacity.",
                    "severity": "WARNING",
                    "metrics": {"clients": clients, "max_cap": max_cap, "latency": lat}
                })
            elif loss >= THRESHOLDS["packet_loss_warning_pct"] or lat >= THRESHOLDS["latency_warning_ms"]:
                detected.append({
                    "ap_id": ap_id,
                    "type": "DEGRADED_PERFORMANCE",
                    "reason": f"Elevated latency ({lat}ms) or packet loss ({loss}%).",
                    "severity": "WARNING",
                    "metrics": {"loss": loss, "latency": lat}
                })
                
        return detected

    def _handle_anomaly_detected(self, snapshot: Dict[str, Any], anomalies: List[Dict[str, Any]]):
        """Processes anomalies, logs pipeline telemetry, and dispatches to Gemini."""
        # Generate an anomaly signature
        sig_parts = [f"{a['ap_id']}:{a['type']}" for a in anomalies]
        current_sig = "|".join(sorted(sig_parts))
        now = time.time()
        
        # Check cooldown to prevent hammering during sustained incidents
        is_new_signature = (current_sig != self.last_incident_signature)
        cooldown_elapsed = (now - self.last_incident_time) > THRESHOLDS["cooldown_seconds"]
        
        if is_new_signature or cooldown_elapsed:
            self.last_incident_signature = current_sig
            self.last_incident_time = now
            self.current_state = "ANOMALY_ACTIVE"
            
            event_id = f"EVT-{int(now)}-{uuid.uuid4().hex[:6].upper()}"
            
            # 1. Antigravity Pipeline Trigger Event
            summary_reasons = "; ".join([f"[{a['ap_id']}] {a['reason']}" for a in anomalies])
            self._emit_event(
                "ANTIGRAVITY_TRIGGER",
                f"⚡ Multi-point anomaly detected by Antigravity Pipeline ({len(anomalies)} breaches): {summary_reasons}",
                "ALERT",
                details={"event_id": event_id, "anomalies": anomalies}
            )
            
            # 2. Package telemetry event payload for Cloud streaming
            event_packet = {
                "event_id": event_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pipeline_agent": "Google Antigravity AIOps Streamer v2.0",
                "probes_state": snapshot,
                "anomalies": anomalies,
                "gateway_info": {
                    "ip": "10.14.0.1",
                    "external_target": "8.8.8.8"
                }
            }
            
            self._emit_event(
                "ANTIGRAVITY_STREAM",
                f"🌐 Streaming incident telemetry payload {event_id} to Gemini Enterprise Cloud...",
                "INFO"
            )
            
            # 3. Call Gemini Cloud RCA Engine
            rca_result = gemini_engine.analyze_incident(event_packet)
            
            # 4. Create enterprise IT ticket
            ticket_id = f"TICK-{time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            new_ticket = {
                "ticket_id": ticket_id,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "OPEN",
                "title": rca_result.get("ticket_title", "Network Anomaly Detected"),
                "severity": rca_result.get("severity", "P2 - High"),
                "root_cause_category": rca_result.get("root_cause_category", "ANOMALY"),
                "root_cause_explanation": rca_result.get("root_cause_explanation", ""),
                "affected_nodes": rca_result.get("affected_nodes", []),
                "blast_radius": rca_result.get("blast_radius", ""),
                "ai_confidence_pct": rca_result.get("ai_confidence_pct", 95.0),
                "remediation_steps": rca_result.get("remediation_steps", []),
                "engine_mode": rca_result.get("engine_mode", "Gemini Cloud"),
                "latest_telemetry": {
                    ap: {"latency_ms": s["latency_ms"], "loss_pct": s["packet_loss_pct"]}
                    for ap, s in snapshot.items()
                }
            }
            
            db.add_ticket(new_ticket)
            
            # 5. Update Student Study Zone Advisories
            if "student_advisories" in rca_result:
                db.update_advisories(rca_result["student_advisories"])
                
            self._emit_event(
                "ANTIGRAVITY_DISPATCH",
                f"✅ Gemini RCA Complete! IT Ticket #{ticket_id} [{new_ticket['severity']}] logged. Student Study Zone Advisory updated.",
                "SUCCESS",
                details={"ticket_id": ticket_id, "severity": new_ticket["severity"]}
            )

    def _handle_healthy_state(self, snapshot: Dict[str, Any]):
        """Runs periodic health heartbeat and handles transition back from an incident."""
        if self.current_state == "ANOMALY_ACTIVE":
            # Recovered back to healthy!
            self.current_state = "HEALTHY"
            self.last_incident_signature = ""
            
            self._emit_event(
                "ANTIGRAVITY_RECOVERY",
                "✨ All campus Wi-Fi telemetry returned to nominal SLA threshold! Probes reporting 100% healthy.",
                "SUCCESS"
            )
            
            # Auto-resolve tickets or mark recovered
            tickets = db.get_tickets()
            for t in tickets:
                if t.get("status") == "OPEN":
                    db.resolve_ticket(t["ticket_id"])
                    
            # Reset student advisories to all optimal
            rca_normal = gemini_engine._run_deterministic_aiops({"probes_state": snapshot})
            db.update_advisories(rca_normal["student_advisories"])
            
        elif random.random() < 0.15: # Periodic telemetry heartbeat
            self._emit_event(
                "PIPELINE_HEARTBEAT",
                f"Heartbeat: Ingested telemetry from 3 AP probes. SLA Compliance: 100%. Latency: {snapshot['AP-A101']['latency_ms']}ms (A), {snapshot['AP-B204']['latency_ms']}ms (B), {snapshot['AP-LIB-G']['latency_ms']}ms (Lib).",
                "INFO"
            )

    def _emit_event(self, event_type: str, message: str, level: str = "INFO", details: Dict[str, Any] = None):
        """Emits an event into the Antigravity pipeline log stream."""
        event = {
            "id": f"EVT-{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "event_type": event_type,
            "message": message,
            "level": level, # "INFO", "ALERT", "SUCCESS", "ERROR"
            "details": details or {}
        }
        db.add_pipeline_event(event)

# Global Antigravity pipeline singleton
pipeline = AntigravityEventPipeline()
