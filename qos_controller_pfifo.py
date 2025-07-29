#!/usr/bin/env python3
import time
import paramiko
import re
from collections import deque

# Configurações
LOG_FILE = "/var/log/tcp_persistent_server.log"
ROUTERS = {
    'r1': '10.0.1.1',
    'r2': '172.16.2.2',
    'r3': '172.16.3.2',
    'r4': '172.16.4.2'
}
USERNAME = "mininet"
PASSWORD = "m1ninetpwd"
LATENCY_HIGH_THRESHOLD = 5.0  # ms
WINDOW_BEFORE_QOS = 10
WINDOW_AFTER_QOS = 50
qos_active = False

latency_buffer = deque(maxlen=WINDOW_BEFORE_QOS)

def ssh_apply_qos(router_ip, enable=True):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(router_ip, username=USERNAME, password=PASSWORD, timeout=5)
        if enable:
            cmd = """
for intf in $(ip -o link show | awk -F': ' '/eth[0-9]+/ {print $2}'); do
  tc qdisc del dev $intf root 2>/dev/null || true
  tc qdisc add dev $intf root handle 1: prio bands 3
  tc filter add dev $intf parent 1: protocol ip prio 1 u32 match ip tos 0xb8 0xff flowid 1:1
  tc filter add dev $intf parent 1: protocol ip prio 2 u32 match ip tos 0x28 0xff flowid 1:2
  tc qdisc add dev $intf parent 1:1 handle 10: pfifo limit 1000
  tc qdisc add dev $intf parent 1:2 handle 20: pfifo limit 5000
done
"""
        else:
            cmd = """
for intf in $(ip -o link show | awk -F': ' '/eth[0-9]+/ {print $2}'); do
  tc qdisc del dev $intf root 2>/dev/null || true
done
"""
        ssh.exec_command(cmd)
    except Exception as e:
        print(f"[ERRO] {router_ip}: {e}")
    finally:
        ssh.close()

def toggle_qos(enable):
    global qos_active
    for name, ip in ROUTERS.items():
        print(f"{'Ativando' if enable else 'Removendo'} QoS em {name} ({ip})...")
        ssh_apply_qos(ip, enable)
    qos_active = enable

def parse_latency(line):
    match = re.search(r'latency=([\d.]+)ms', line)
    return float(match.group(1)) if match else None

def main():
    global latency_buffer, qos_active
    print("[*] Iniciando monitoramento do log de latência...")

    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)  # Vai para o final do arquivo
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue

            latency = parse_latency(line)
            if latency is None:
                continue

            latency_buffer.append(latency)
            avg_latency = sum(latency_buffer) / len(latency_buffer)
            print(f"[INFO] Média ({len(latency_buffer)}): {avg_latency:.3f} ms")

            # Lógica de ativação/desativação do QoS
            if not qos_active and len(latency_buffer) == WINDOW_BEFORE_QOS and avg_latency > LATENCY_HIGH_THRESHOLD:
                print("[ALERTA] Média alta detectada — Ativando QoS...")
                toggle_qos(True)
                latency_buffer = deque(maxlen=WINDOW_AFTER_QOS)

            elif qos_active and len(latency_buffer) == WINDOW_AFTER_QOS and avg_latency < LATENCY_HIGH_THRESHOLD:
                print("[OK] Média baixa detectada — Desativando QoS...")
                toggle_qos(False)
                latency_buffer = deque(maxlen=WINDOW_BEFORE_QOS)

if __name__ == "__main__":
    main()