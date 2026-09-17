#!/usr/bin/env python3
"""
© AngelaMos | 2026
tools/detect_beacon.py

Behavioral C2 beacon detection tool using Scapy to analyze packet timings,
payload sizes, and URI patterns (Challenge 11).
"""

import logging
import statistics
from collections import defaultdict
import time
from scapy.all import IP, TCP, sniff, Raw

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("detect_beacon")

# Store packet timestamps and sizes per source IP
source_tracker = defaultdict(lambda: {"timestamps": [], "sizes": []})

# Detection thresholds
BEACON_PORT = 47431  # Matches your C2 server port configuration
STD_DEV_THRESHOLD = 0.5  # Low standard deviation indicates regular automated heartbeats
MIN_SAMPLES = 5

def analyze_packet(packet):
    if IP in packet and TCP in packet:
        src_ip = packet[IP].src
        dst_port = packet[TCP].dport
        src_port = packet[TCP].sport

        # Filter traffic targeting or originating from our C2 port
        if dst_port == BEACON_PORT or src_port == BEACON_PORT:
            payload_len = len(packet[TCP].payload)
            current_time = time.time()

            # Inspect raw TCP payload for WebSocket upgrade path signatures
            if Raw in packet:
                try:
                    payload_str = packet[Raw].load.decode("utf-8", errors="ignore")
                    if "/ws/beacon" in payload_str:
                        logger.warning(
                            "[ALERT] WebSocket upgrade path '/ws/beacon' detected from IP: %s",
                            src_ip
                        )
                except Exception:
                    pass

            # Track timing and payload size for behavioral rhythm analysis
            if payload_len > 0:
                client_ip = src_ip if src_port != BEACON_PORT else packet[IP].dst
                tracker = source_tracker[client_ip]
                tracker["timestamps"].append(current_time)
                tracker["sizes"].append(payload_len)

                # Maintain a rolling window of the last 20 samples
                if len(tracker["timestamps"]) > 20:
                    tracker["timestamps"].pop(0)
                    tracker["sizes"].pop(0)

                # Analyze inter-arrival intervals once minimum sample size is reached
                if len(tracker["timestamps"]) >= MIN_SAMPLES:
                    timestamps = tracker["timestamps"]
                    intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                    
                    mean_interval = statistics.mean(intervals)
                    std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0

                    # Flag low variance in inter-message timing (typical of beacon jitter patterns)
                    if std_dev < STD_DEV_THRESHOLD and mean_interval < 15:
                        logger.warning(
                            "[ALERT] Periodic beacon pattern detected from %s! Mean Interval: %.2fs, StdDev: %.2fs, Payload Sizes: %s",
                            client_ip, mean_interval, std_dev, set(tracker["sizes"])
                        )

def main():
    logger.info("Starting C2 Beacon Detection Tool on port %d...", BEACON_PORT)
    logger.info("Press Ctrl+C to stop sniffing network traffic.")
    # Sniff TCP traffic on the designated port (requires root privileges for raw sockets)
    sniff(filter=f"tcp port {BEACON_PORT}", prn=analyze_packet, store=False)

if __name__ == "__main__":
    main()