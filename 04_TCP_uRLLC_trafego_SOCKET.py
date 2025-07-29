#!/usr/bin/env python3
import time
import socket
import argparse

def main():
    parser = argparse.ArgumentParser(description='Cliente TCP uRLLC')
    parser.add_argument('--server', required=True, help='IP do servidor')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor')
    parser.add_argument('--interval', type=float, default=0.5, help='Intervalo entre pacotes')
    parser.add_argument('--size', type=int, default=128, help='Tamanho do payload')
    args = parser.parse_args()

    print(f"Conectando a {args.server}:{args.port}...")
    
    # Configurar socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Definir opções de socket
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Desabilitar Nagle
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)     # Priorização ToS
    
    # Configurar timeout
    sock.settimeout(5.0)
    
    try:
        # Estabelecer conexão
        sock.connect((args.server, args.port))
        print("Conexão estabelecida. Iniciando envio de dados...")
        
        packet_count = 0
        start_time = time.time()
        
        try:
            while True:
                # Criar payload com timestamp
                timestamp = time.perf_counter()
                payload = str(timestamp).ljust(args.size).encode()
                
                # Enviar dados
                sock.sendall(payload)
                packet_count += 1
                
                # Feedback a cada 10 pacotes
                if packet_count % 10 == 0:
                    print(f"Enviados {packet_count} pacotes | Último: {timestamp:.6f}")
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\nEnvio interrompido pelo usuário")
        except BrokenPipeError:
            print("\nConexão fechada pelo servidor")
        except socket.timeout:
            print("\nTimeout de conexão")
        finally:
            sock.close()
            duration = time.time() - start_time
            print(f"\nResumo: {packet_count} pacotes em {duration:.2f}s")
            print(f"Taxa média: {packet_count/duration:.2f} pps")
            
    except ConnectionRefusedError:
        print(f"Conexão recusada. Verifique se o servidor está ativo em {args.server}:{args.port}")
    except socket.timeout:
        print("Timeout de conexão. Verifique a rede e firewall.")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()