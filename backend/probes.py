"""Simulated IoT and Network Telemetry Probes.
Continuously generates high-fidelity telemetry for Block A, Block B, and Library APs.
"""

import random
import time
from typing import Dict, Any, List
from backend.config import AP_NODES, CAMPUS_GATEWAY
from backend.storage import db
from backend.interpreter import interpreter

class ProbeSimulator:
    def __init__(self):
        self.tick_counter = 0

    def generate_probe_telemetry(self, ap_id: str, scenario: str) -> Dict[str, Any]:
        """Generates realistic telemetry for a specific AP based on the active scenario."""
        node_meta = AP_NODES[ap_id]
        now_ts = time.time()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_ts))
        
        # Base healthy telemetry values
        latency = round(random.uniform(14.0, 22.0), 1)
        packet_loss = round(random.uniform(0.0, 0.4), 1)
        rssi = round(random.uniform(-62.0, -56.0), 1)
        clients = node_meta["nominal_clients"] + random.randint(-4, 6)
        channel_util = round(random.uniform(22.0, 38.0), 1)
        tx_rate = round(random.uniform(280.0, 450.0), 1)
        rx_rate = round(random.uniform(120.0, 220.0), 1)
        dns_status = "OK"
        gateway_reachability = True
        status_label = "HEALTHY"
        syslogs: List[str] = [
            f"[{time.strftime('%H:%M:%S')}] [INFO] hostapd: STA authenticated successfully (AES-CCMP / 802.11ax)",
            f"[{time.strftime('%H:%M:%S')}] [INFO] wlan0: Channel {node_meta['channel_5g']} clean, noise floor -98 dBm"
        ]

        # Apply Scenario Overrides
        if scenario == "BLOCK_B_HARDWARE_FAILURE":
            if ap_id == "AP-B204":
                # Catastrophic hardware & radio failure on Block B
                status_label = "CRITICAL_FAILURE"
                latency = 999.0 # Timeout
                packet_loss = 100.0
                rssi = -95.0
                clients = 0
                channel_util = 0.0
                tx_rate = 0.0
                rx_rate = 0.0
                dns_status = "TIMEOUT"
                gateway_reachability = False
                syslogs = [
                    f"[{time.strftime('%H:%M:%S')}] [CRIT] ath11k_pci 0000:01:00.0: Target firmware crashed! (assert: 0xDEADBEEF, pc: 0x8003F412)",
                    f"[{time.strftime('%H:%M:%S')}] [ALERT] kernel: PCIe AER uncorrectable fatal hardware error on radio transceivers [Bus 0x01]",
                    f"[{time.strftime('%H:%M:%S')}] [ERR] hostapd: nl80211: Driver failed to respond to beacon update ioctl (No such device)",
                    f"[{time.strftime('%H:%M:%S')}] [CRIT] watchdog: AP-B204 hardware watchdog failed power-cycle reset sequence!"
                ]
            else:
                # Other blocks remain healthy and normal
                status_label = "HEALTHY"

        elif scenario == "CAMPUS_ISP_OUTAGE":
            # Campus-wide ISP backhaul degradation across all APs
            status_label = "DEGRADED"
            latency = round(random.uniform(340.0, 520.0), 1)
            packet_loss = round(random.uniform(22.0, 38.0), 1)
            # Local radio signal is still strong because physical APs are fine!
            rssi = round(random.uniform(-60.0, -55.0), 1)
            dns_status = "TIMEOUT"
            gateway_reachability = False
            tx_rate = round(random.uniform(10.0, 25.0), 1)
            rx_rate = round(random.uniform(5.0, 15.0), 1)
            syslogs = [
                f"[{time.strftime('%H:%M:%S')}] [WARN] netmon: WAN border gateway 10.14.0.1 BGP peer flapping (NREN optical hold timer expired)",
                f"[{time.strftime('%H:%M:%S')}] [WARN] dnsmasq: upstream DNS 8.8.8.8 query timed out after 4000ms",
                f"[{time.strftime('%H:%M:%S')}] [ERR] uplink: Fiber interface TenGigabitEthernet0/1/0 RX optical power low (-28.6 dBm)"
            ]

        elif scenario == "LIBRARY_CONGESTION":
            if ap_id == "AP-LIB-G":
                # High density student overload in the library
                status_label = "CONGESTED"
                clients = random.randint(280, 310) # Over capacity (220)
                channel_util = round(random.uniform(94.0, 99.2), 1)
                latency = round(random.uniform(82.0, 145.0), 1)
                packet_loss = round(random.uniform(6.5, 12.0), 1)
                rssi = round(random.uniform(-74.0, -68.0), 1)
                tx_rate = round(random.uniform(35.0, 75.0), 1)
                rx_rate = round(random.uniform(40.0, 80.0), 1)
                dns_status = "SLOW"
                syslogs = [
                    f"[{time.strftime('%H:%M:%S')}] [WARN] wlan0: High BSS co-channel interference detected (airtime duty cycle {channel_util}%)",
                    f"[{time.strftime('%H:%M:%S')}] [WARN] hostapd: Station association limit reached for BSSID {node_meta['mac']} ({clients} active clients)",
                    f"[{time.strftime('%H:%M:%S')}] [WARN] qos: WMM voice/video queue buffer overrun, dropped 184 frames in 1000ms"
                ]
            else:
                # Block A and Block B remain completely clear
                status_label = "HEALTHY"

        telemetry = {
            "ap_id": ap_id,
            "name": node_meta["name"],
            "zone": node_meta["zone"],
            "model": node_meta["model"],
            "ip": node_meta["ip"],
            "mac": node_meta["mac"],
            "timestamp": now_str,
            "epoch": now_ts,
            "status": status_label,
            "latency_ms": latency,
            "packet_loss_pct": packet_loss,
            "rssi_dbm": rssi,
            "connected_clients": clients,
            "max_capacity": node_meta["max_capacity"],
            "channel_utilization_pct": channel_util,
            "tx_rate_mbps": tx_rate,
            "rx_rate_mbps": rx_rate,
            "dns_status": dns_status,
            "gateway_reachability": gateway_reachability,
            "syslog_entries": syslogs
        }
        return telemetry

    def poll_all_probes(self) -> Dict[str, Any]:
        """Polls simulated probes across Block A, Block B, and Library, recording in DB."""
        scenario_info = db.get_scenario()
        active_scenario = scenario_info["name"]
        
        snapshot = {}
        for ap_id in AP_NODES.keys():
            t_record = self.generate_probe_telemetry(ap_id, active_scenario)
            db.record_telemetry(ap_id, t_record)
            snapshot[ap_id] = t_record

            # Interpret and record logs with Initial AI Results
            # During anomalies, record all logs immediately.
            # During normal baseline, sample logs every 3 ticks to avoid flooding.
            should_record_logs = (active_scenario != "NORMAL") or (self.tick_counter % 3 == 0)
            if should_record_logs and t_record.get("syslog_entries"):
                for raw_log in t_record["syslog_entries"]:
                    interpreted_entry = interpreter.interpret_log(
                        raw_log=raw_log,
                        ap_id=ap_id,
                        timestamp=time.strftime("%H:%M:%S")
                    )
                    db.add_interpreted_log(interpreted_entry)
            
        self.tick_counter += 1
        return snapshot

# Global probe simulator singleton
probes = ProbeSimulator()
