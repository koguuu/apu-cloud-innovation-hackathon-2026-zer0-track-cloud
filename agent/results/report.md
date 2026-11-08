# Agent evaluation report

Generated 2026-11-07 16:04 | model: backend default | runs per scenario: 3

| scenario | rules said | gemini said | confidence | final | expected | result |
|---|---|---|---|---|---|---|
| ap_failure | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |
| ap_failure | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |
| ap_failure | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |
| ap_looks_like_congestion | ap_hardware_failure | congestion | high | congestion | congestion | OK |
| ap_looks_like_congestion | ap_hardware_failure | congestion | high | congestion | congestion | OK |
| ap_looks_like_congestion | ap_hardware_failure | congestion | high | congestion | congestion | OK |
| congestion | congestion | congestion | high | congestion | congestion | OK |
| congestion | congestion | congestion | high | congestion | congestion | OK |
| congestion | congestion | congestion | high | congestion | congestion | OK |
| congestion_moderate_loss | congestion | congestion | high | congestion | congestion | OK |
| congestion_moderate_loss | congestion | congestion | high | congestion | congestion | OK |
| congestion_moderate_loss | congestion | congestion | high | congestion | congestion | OK |
| iot_fault | iot_device_fault | iot_device_fault | high | iot_device_fault | iot_device_fault | OK |
| iot_fault | iot_device_fault | iot_device_fault | high | iot_device_fault | iot_device_fault | OK |
| iot_fault | iot_device_fault | iot_device_fault | high | iot_device_fault | iot_device_fault | OK |
| uplink_outage | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| uplink_outage | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| uplink_outage | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| uplink_two_locations | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| uplink_two_locations | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| uplink_two_locations | isp_uplink_outage | isp_uplink_outage | high | isp_uplink_outage | isp_uplink_outage | OK |
| weak_signal_single_ap | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |
| weak_signal_single_ap | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |
| weak_signal_single_ap | ap_hardware_failure | ap_hardware_failure | high | ap_hardware_failure | ap_hardware_failure | OK |

## Summary

- Runs: 24   Gemini answered: 24/24   Gemini text used in the ticket: 24/24
- Rules correct:             21/24
- Gemini's own answer correct: 24/24
- Final cause correct:       24/24   (after guard rails; NOT the same as Gemini accuracy)
- Gemini disagreed with rules: 3   Overrides applied: 3   Blocked by guard rails: 0
- Explanations citing numbers/thresholds not in the evidence: 0/24

## Text written for each ticket (last run)

**ap_failure** (gemini)
- Explanation: Access point ap-b-02 at Block B has 100% packet loss and a very weak signal of -90 dBm, whereas neighbouring APs ap-b-01 and ap-b-03 are healthy with low packet loss of 0.4% and 0.6% and strong signals of -57 dBm and -60 dBm. Congestion was ruled out because the packet loss is 100% and the signal is very weak instead of low and good.
- Action: Dispatch a technician to replace the faulty hardware for access point ap-b-02 in Block B.

**ap_looks_like_congestion** (gemini)
- Explanation: Access point ap-a-03 in Block A shows high latency of 420 ms with 52 clients, but packet loss is low at 1.5% and the signal is strong at -54 dBm. Hardware failure was ruled out because packet loss is only 1.5% and the signal is strong.
- Action: Investigate client load distribution on access point ap-a-03 and consider load balancing traffic to nearby healthy access points.

**congestion** (gemini)
- Explanation: APs in block-a exhibit high latency up to 310 ms, but packet loss remains low at 1.2% and 0.9%, and signals are strong at -52 dBm and -55 dBm with high client counts of 96 and 88. Hardware failure is ruled out because packet loss is low and signals are strong.
- Action: Balance the client load across surrounding access points in Block A to reduce latency.

**congestion_moderate_loss** (gemini)
- Explanation: Access points ap-b-01 and ap-b-03 show high latency with low packet loss of 2.5% and 2.1% and a strong signal of -58 dBm and -61 dBm while supporting 92 and 85 clients. Hardware failure is ruled out because packet loss remains low and the signal is strong.
- Action: Deploy additional access points or implement load balancing in Block B to distribute the 177 combined clients and reduce latency.

**iot_fault** (gemini)
- Explanation: The card reader and sensor are down while Wi-Fi health is good, which rules out network-wide or AP-level connectivity issues. Therefore, the incident is isolated to the specific IoT devices rather than the wireless infrastructure.
- Action: Dispatch a technician to inspect and reboot the offline card reader and sensor in the IoT Lab.

**uplink_outage** (gemini)
- Explanation: APs across block-a, block-b, lab-cyber, and lab-network degraded simultaneously with high packet loss between 65% and 80%, pointing to a shared uplink issue. Single-location hardware failure was ruled out because multiple distinct locations are affected at the same time.
- Action: Contact the primary ISP provider to check the campus upstream connection and router status.

**uplink_two_locations** (gemini)
- Explanation: Multiple APs across different locations experienced severe degradation with high latency of 980 ms and 1010 ms alongside packet loss of 55% and 60%, indicating a shared uplink failure. Single-site causes like hardware failure or congestion were ruled out because two separate locations were simultaneously impacted.
- Action: Contact the upstream internet service provider to investigate the campus uplink connection and check core routing equipment.

**weak_signal_single_ap** (gemini)
- Explanation: AP ap-cy-02 at the Cybersecurity Lab exhibits a very weak signal of -88 dBm with 4 clients, while the neighboring AP ap-cy-01 is healthy with a strong signal of -55 dBm and 17 clients. Congestion was ruled out because the signal strength is poor rather than good.
- Action: Dispatch a technician to inspect and replace the faulty hardware for access point ap-cy-02.
