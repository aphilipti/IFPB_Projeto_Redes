#!/usr/bin/env python3
from scapy.all import sniff, IP, TCP
from datetime import datetime
from threading import Timer
from collections import defaultdict

# Configurações
INTERFACE = "eth1"
PORT = 5000
TOS_URRLC = 0xB8
LOG_FILE = "/var/log/urllc_tcp_window_stats.log"
INTERVAL = 5  # segundos

# Armazena contadores por (src, dst)
stats = defaultdict(lambda: {"count": 0, "sum_window": 0, "sum_length": 0})

def log_and_reset_stats():
    timestamp = datetime.now().isoformat()

    for key, data in stats.items():
        src, dst = key
        count = data["count"]
        avg_window = data["sum_window"] / count if count > 0 else 0
        avg_length = data["sum_length"] / count if count > 0 else 0
        pps = count / INTERVAL

        line = (f"{timestamp} src={src} dst={dst} "
                f"avg_window={avg_window:.1f} avg_length={avg_length:.1f} pps={pps:.2f}")
        print(line)

        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")

    stats.clear()
    Timer(INTERVAL, log_and_reset_stats).start()

def handle_packet(pkt):
    if IP in pkt and TCP in pkt:
        ip = pkt[IP]
        tcp = pkt[TCP]

        if tcp.dport == PORT and ip.tos == TOS_URRLC:
            key = (ip.src, ip.dst)
            stats[key]["count"] += 1
            stats[key]["sum_window"] += tcp.window
            stats[key]["sum_length"] += len(tcp.payload)

def main():
    print(f"[*] Escutando interface {INTERFACE} para pacotes URLLC (TOS=0xB8)...")
    Timer(INTERVAL, log_and_reset_stats).start()
    sniff(iface=INTERFACE, filter=f"tcp port {PORT}", prn=handle_packet, store=False)

if __name__ == "__main__":
    main()
