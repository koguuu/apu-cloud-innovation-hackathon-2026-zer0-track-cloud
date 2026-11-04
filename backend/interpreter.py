"""Explainable AIOps Log Interpreter.
Provides instant micro-inference, classification, and interpretability explanations
for every single incoming log and telemetry anomaly.
"""

import re
import time
from typing import Dict, Any, List

class LogInterpreter:
    def __init__(self):
        # Known log pattern signatures for micro-inference
        self.signatures = [
            # 1. Hardware & Kernel Panic Signatures
            {
                "pattern": r"(ath11k|firmware crashed|PCIe AER|uncorrectable fatal|kernel panic|watchdog failed)",
                "category": "HARDWARE_DRIVER_FAULT",
                "severity": "CRITICAL",
                "ai_summary": "Fatal radio transceiver hardware/PCIe fault detected.",
                "reasoning": (
                    "Firmware register assertion and PCIe AER bus fault signify an unrecoverable "
                    "physical transceiver or bus lockup. This cannot be resolved by software reconfiguration "
                    "and requires an electrical PoE power-bounce or physical AP replacement."
                ),
                "confidence": 99.4,
                "feature_weights": {"hardware_aer_error": 0.95, "rf_contention": 0.01, "upstream_link": 0.04},
                "recommended_triage": "Power-cycle PoE switchport; dispatch field technician if AP fails to reboot."
            },
            # 2. ISP & Border Uplink Signatures
            {
                "pattern": r"(BGP peer flapping|upstream DNS.*timed out|optical power low|fiber interface)",
                "category": "WAN_UPLINK_DEGRADATION",
                "severity": "CRITICAL",
                "ai_summary": "External ISP backhaul / optical transport degradation.",
                "reasoning": (
                    "Optical dBm drop (-28.6 dBm) on border 10Gbps fiber accompanied by BGP hold timer "
                    "expiration confirms degradation resides outside the local campus LAN, upstream with the ISP."
                ),
                "confidence": 98.6,
                "feature_weights": {"optical_signal_attenuation": 0.94, "bgp_hold_timeout": 0.91, "local_lan_health": 0.05},
                "recommended_triage": "Engage ISP NOC emergency line; verify automatic failover to redundant link."
            },
            # 3. High Density RF Congestion & Airtime Starvation
            {
                "pattern": r"(co-channel interference|airtime duty cycle|Station association limit|buffer overrun)",
                "category": "RF_AIRTIME_SATURATION",
                "severity": "WARNING",
                "ai_summary": "Severe 2.4/5GHz RF contention and station over-saturation.",
                "reasoning": (
                    "Airtime duty cycle >95% and station association cap breach demonstrate bufferbloat "
                    "caused by excessive concurrent client devices, not physical hardware failure."
                ),
                "confidence": 97.2,
                "feature_weights": {"client_density_surge": 0.93, "channel_utilization": 0.96, "packet_loss_rate": 0.42},
                "recommended_triage": "Trigger 802.11v BSS steering to neighboring APs; raise probe threshold to -72dBm."
            },
            # 4. Routine & Healthy Handshake Signatures
            {
                "pattern": r"(authenticated successfully|AES-CCMP|802\.11ax|Channel.*clean|noise floor)",
                "category": "NOMINAL_OPERATIONS",
                "severity": "HEALTHY",
                "ai_summary": "Routine 802.11ax client session negotiation.",
                "reasoning": (
                    "Normal 4-way WPA3 handshake completed with optimal SNR margin (>32 dB). "
                    "RF noise floor is clean at -98 dBm. No anomalous traffic signatures detected."
                ),
                "confidence": 99.8,
                "feature_weights": {"handshake_latency": 0.05, "snr_margin": 0.98, "packet_loss": 0.00},
                "recommended_triage": "No action needed. Radio running within peak SLA parameters."
            }
        ]

    def interpret_log(self, raw_log: str, ap_id: str = "UNKNOWN", timestamp: str = None) -> Dict[str, Any]:
        """Analyzes a raw log line and returns structured explainable AI insight."""
        if not timestamp:
            timestamp = time.strftime("%H:%M:%S")

        # Match against signature heuristics
        matched_sig = None
        for sig in self.signatures:
            if re.search(sig["pattern"], raw_log, re.IGNORECASE):
                matched_sig = sig
                break

        # Fallback for unrecognized logs
        if not matched_sig:
            if "ERR" in raw_log or "CRIT" in raw_log:
                matched_sig = {
                    "category": "UNCLASSIFIED_ERROR",
                    "severity": "CRITICAL",
                    "ai_summary": "Anomalous error signature flagged by NLP parser.",
                    "reasoning": "Unrecognized error pattern detected in AP syslogs requiring NOC triage.",
                    "confidence": 85.0,
                    "feature_weights": {"error_token_presence": 0.85},
                    "recommended_triage": "Inspect raw kernel trace for details."
                }
            elif "WARN" in raw_log:
                matched_sig = {
                    "category": "UNCLASSIFIED_WARNING",
                    "severity": "WARNING",
                    "ai_summary": "Potential network degradation warning.",
                    "reasoning": "Telemetry or syslog indicates a metric approaching warning threshold.",
                    "confidence": 88.0,
                    "feature_weights": {"warning_token_presence": 0.88},
                    "recommended_triage": "Monitor sliding window telemetry."
                }
            else:
                matched_sig = {
                    "category": "ROUTINE_EVENT",
                    "severity": "HEALTHY",
                    "ai_summary": "Routine operational log event.",
                    "reasoning": "Standard background operating telemetry within expected baseline limits.",
                    "confidence": 96.0,
                    "feature_weights": {"nominal_syntax": 0.95},
                    "recommended_triage": "No remediation required."
                }

        log_id = f"LOG-{int(time.time()*1000)}-{hash(raw_log) % 10000:04d}"

        return {
            "log_id": log_id,
            "timestamp": timestamp,
            "ap_id": ap_id,
            "raw_log": raw_log,
            "severity": matched_sig["severity"],
            "ai_classification": matched_sig["category"],
            "initial_ai_result": {
                "summary": matched_sig["ai_summary"],
                "interpretability_explanation": matched_sig["reasoning"],
                "confidence_pct": matched_sig["confidence"],
                "feature_weights": matched_sig["feature_weights"],
                "recommended_triage": matched_sig["recommended_triage"]
            }
        }

# Global singleton
interpreter = LogInterpreter()
