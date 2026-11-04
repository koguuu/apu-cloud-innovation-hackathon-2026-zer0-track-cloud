"""Automated Unit and Pipeline Verification Test Suite.
Tests simulated IoT probes, scenario injection, Antigravity anomaly detection,
Gemini RCA generation, and ticket creation.
"""

import sys
import os
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.config import AP_NODES
from backend.storage import db
from backend.probes import probes
from backend.pipeline import pipeline
from backend.aiops_gemini import gemini_engine
from backend.interpreter import interpreter

def run_tests():
    print("==========================================================")
    print(" Running Campus Wi-Fi Health AIOps Pipeline Test Suite...")
    print("==========================================================")

    # Test 1: Verify AP Probes Generation
    print("\n[Test 1] Polling simulated probes in NORMAL baseline mode...")
    db.set_scenario("NORMAL")
    snapshot = probes.poll_all_probes()
    assert len(snapshot) == 3, f"Expected 3 AP probes, got {len(snapshot)}"
    for ap_id, data in snapshot.items():
        assert data["latency_ms"] < 40, f"Latency too high in normal mode: {data['latency_ms']}ms"
        assert data["packet_loss_pct"] < 2.0, f"Packet loss too high in normal: {data['packet_loss_pct']}%"
        print(f"  ✓ {ap_id} ({data['name']}): Latency={data['latency_ms']}ms, Loss={data['packet_loss_pct']}%, RSSI={data['rssi_dbm']}dBm, Clients={data['connected_clients']}")
    print("  -> Test 1 Passed: Normal baseline probes nominal.")

    # Test 2: Test Scenario Injection (Block B Hardware Failure)
    print("\n[Test 2] Injecting BLOCK_B_HARDWARE_FAILURE scenario...")
    db.set_scenario("BLOCK_B_HARDWARE_FAILURE")
    crash_snapshot = probes.poll_all_probes()
    
    b204 = crash_snapshot["AP-B204"]
    a101 = crash_snapshot["AP-A101"]
    lib = crash_snapshot["AP-LIB-G"]
    
    assert b204["packet_loss_pct"] == 100.0, f"Expected 100% loss on AP-B204, got {b204['packet_loss_pct']}"
    assert a101["packet_loss_pct"] < 2.0, f"Block A should be unaffected, got {a101['packet_loss_pct']}"
    assert lib["packet_loss_pct"] < 2.0, f"Library should be unaffected, got {lib['packet_loss_pct']}"
    print(f"  ✓ AP-B204 successfully failed (Loss={b204['packet_loss_pct']}%, Latency={b204['latency_ms']}ms, Status={b204['status']})")
    print(f"  ✓ Block A & Library confirmed healthy.")
    print("  -> Test 2 Passed: Hardware failure isolated to Block B.")

    # Test 3: Test Antigravity Anomaly Detection
    print("\n[Test 3] Testing Antigravity anomaly evaluation engine...")
    anomalies = pipeline._evaluate_anomalies(crash_snapshot)
    assert len(anomalies) >= 1, "Antigravity failed to detect critical SLA breach!"
    print(f"  ✓ Antigravity detected {len(anomalies)} breach(es): {anomalies[0]['reason']}")
    print("  -> Test 3 Passed: Antigravity pipeline anomaly detection confirmed.")

    # Test 4: Test Gemini RCA Root Cause Analysis
    print("\n[Test 4] Testing Gemini Enterprise RCA engine...")
    event_packet = {
        "event_id": "TEST-EVT-001",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "probes_state": crash_snapshot,
        "anomalies": anomalies
    }
    rca = gemini_engine.analyze_incident(event_packet)
    assert rca["root_cause_category"] == "HARDWARE_FAILURE", f"Unexpected RCA category: {rca['root_cause_category']}"
    assert "AP-B204" in rca["affected_nodes"], "AP-B204 not flagged in affected nodes!"
    assert rca["ai_confidence_pct"] > 90, "AI confidence below 90%"
    assert "student_advisories" in rca, "Missing student advisories in RCA output!"
    assert rca["student_advisories"]["zones"]["Block B"]["recommendation"] == "AVOID", "Block B was not marked as AVOID for students!"
    print(f"  ✓ Ticket Title: {rca['ticket_title']}")
    print(f"  ✓ Severity: {rca['severity']}")
    print(f"  ✓ Root Cause: {rca['root_cause_explanation'][:90]}...")
    print(f"  ✓ AI Confidence: {rca['ai_confidence_pct']}%")
    print(f"  ✓ Student Advisory Headline: {rca['student_advisories']['headline']}")
    print("  -> Test 4 Passed: Gemini RCA and Student Advisories accurately generated.")

    # Test 5: Test Campus ISP Outage Scenario
    print("\n[Test 5] Testing CAMPUS_ISP_OUTAGE scenario...")
    db.set_scenario("CAMPUS_ISP_OUTAGE")
    isp_snapshot = probes.poll_all_probes()
    isp_event_packet = {
        "event_id": "TEST-EVT-002",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "probes_state": isp_snapshot,
        "anomalies": pipeline._evaluate_anomalies(isp_snapshot)
    }
    isp_rca = gemini_engine.analyze_incident(isp_event_packet)
    assert isp_rca["root_cause_category"] == "ISP_BACKHAUL_DEGRADATION", f"Unexpected RCA: {isp_rca['root_cause_category']}"
    assert isp_rca["severity"] == "P1 - Critical", f"Expected P1, got {isp_rca['severity']}"
    print(f"  ✓ Correctly identified global ISP outage: {isp_rca['ticket_title']}")
    print("  -> Test 5 Passed: Campus ISP degradation correctly differentiated from local AP failure.")

    # Test 6: Test Explainable AI Log Interpretability Engine
    print("\n[Test 6] Testing Explainable AI (XAI) Log Interpreter...")
    sample_log = "[CRIT] ath11k_pci 0000:01:00.0: Target firmware crashed! (assert: 0xDEADBEEF)"
    interp = interpreter.interpret_log(sample_log, ap_id="AP-B204")
    assert interp["ai_classification"] == "HARDWARE_DRIVER_FAULT", f"Unexpected classification: {interp['ai_classification']}"
    assert interp["initial_ai_result"]["confidence_pct"] > 95, "Confidence score too low"
    assert "feature_weights" in interp["initial_ai_result"], "Missing feature weights"
    assert "hardware_aer_error" in interp["initial_ai_result"]["feature_weights"]
    print(f"  ✓ Raw Log: {interp['raw_log']}")
    print(f"  ✓ AI Classification: {interp['ai_classification']}")
    print(f"  ✓ Initial AI Insight: {interp['initial_ai_result']['summary']}")
    print(f"  ✓ Explainable Reasoning: {interp['initial_ai_result']['interpretability_explanation'][:80]}...")
    print(f"  ✓ Confidence: {interp['initial_ai_result']['confidence_pct']}%")
    print(f"  ✓ Signal Weights: {interp['initial_ai_result']['feature_weights']}")
    print("  -> Test 6 Passed: Instant AI Log Interpretability verified.")

    # Test 7: End-to-End Live Pipeline Worker Loop
    print("\n[Test 7] Testing End-to-End Background Pipeline Worker Loop...")
    pipeline.start()
    time.sleep(1.0)
    db.set_scenario("BLOCK_B_HARDWARE_FAILURE")
    time.sleep(3.5)
    
    live_tickets = [t for t in db.get_tickets() if t["status"] == "OPEN"]
    assert len(live_tickets) > 0, "Pipeline worker failed to create open ticket during failure scenario!"
    print(f"  ✓ Pipeline background daemon automatically generated ticket: {live_tickets[0]['ticket_id']} ({live_tickets[0]['title']})")
    
    db.set_scenario("NORMAL")
    time.sleep(3.5)
    resolved = [t for t in db.get_tickets() if t["status"] == "RESOLVED"]
    assert len(resolved) > 0, "Pipeline worker failed to auto-resolve ticket after returning to normal!"
    print(f"  ✓ Pipeline automatically auto-resolved ticket upon recovery: {resolved[0]['ticket_id']}")
    pipeline.stop()
    print("  -> Test 7 Passed: End-to-end background worker loop verified.")

    # Reset to normal
    db.set_scenario("NORMAL")
    print("\n==========================================================")
    print(" ✨ ALL TESTS PASSED SUCCESSFULLY! (7/7)")
    print("==========================================================")

if __name__ == "__main__":
    run_tests()
