#!/usr/bin/env python3
import time
import socket
import argparse
from scapy.all import Raw

def main():
    parser = argparse.ArgumentParser(description='Cliente TCP uRLLC (híbrido Scapy + socket)')
    parser.add_argument('--server', required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor')
    parser.add_argument('--interval', type=float, default=0.5, help='Intervalo entre pacotes')
    parser.add_argument('--size', type=int, default=128, help='Tamanho do payload')
    args = parser.parse_args()

    print(f"Conectando a {args.server}:{args.port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
    sock.settimeout(5.0)

    try:
        sock.connect((args.server, args.port))
        print("Conexão estabelecida. Iniciando envio de dados...")

        packet_count = 0
        start_time = time.time()

        try:
            while True:
                timestamp = time.perf_counter()
                payload_raw = Raw(str(timestamp).ljust(args.size).encode())

                # Apenas usamos o conteúdo do Raw, sem montar IP/TCP
                sock.sendall(bytes(payload_raw))
                packet_count += 1

                if packet_count % 10 == 0:
                    print(f"Enviados {packet_count} pacotes | Último timestamp: {timestamp:.6f}")

                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nEnvio interrompido pelo usuário")
        except (BrokenPipeError, socket.timeout):
            print("\nConexão encerrada ou timeout.")
        finally:
            sock.close()
            duration = time.time() - start_time
            print(f"\nResumo: {packet_count} pacotes enviados em {duration:.2f}s")
            print(f"Taxa média: {packet_count/duration:.2f} pps")

    except ConnectionRefusedError:
        print(f"Conexão recusada. Verifique se o servidor está ativo em {args.server}:{args.port}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()