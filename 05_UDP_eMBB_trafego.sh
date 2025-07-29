#!/bin/bash
# Gerador de tráfego eMBB com múltiplos fluxos UDP
# TOS: 0x28 (DSCP AF11) - Prioridade média

# Configurações
DEST_IP="10.0.1.2"
BASE_PORT=5201
PARALLEL=5                 # Fluxos simultâneos
DURATION=60                # Segundos
BANDWIDTH="10M"            # Por fluxo
TOS=40                     # 0x28 = AF11 (binário: 00101000)
PACKET_SIZE=1400           # Bytes

echo "[*] Iniciando $PARALLEL fluxos UDP eMBB"
echo "    Destino: $DEST_IP"
echo "    Banda total: $((PARALLEL * ${BANDWIDTH%%M*}))M"
echo "    TOS: 0x$(printf '%x' $TOS) (DSCP AF11)"

# Iniciar fluxos em background
for i in $(seq 1 $PARALLEL); do
  PORT=$((BASE_PORT + i - 1))
  echo "  [Fluxo $i] Porta $PORT | Banda $BANDWIDTH"
  
  iperf3 -c "$DEST_IP" \
    -u \
    -b "$BANDWIDTH" \
    -t "$DURATION" \
    -p "$PORT" \
    --tos "$TOS" \
    -l "$PACKET_SIZE" > /dev/null 2>&1 &
done

echo "[*] Tráfego em execução. Aguardando término..."
wait
echo "[+] Todos os fluxos concluídos"