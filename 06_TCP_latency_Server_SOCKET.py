#!/usr/bin/env python3
import socket
import time
import logging
import os
import sys
from threading import Thread

# Configurações
PORT = 5000
LOG_FILE = "/var/log/tcp_persistent_server.log"
MAX_CONNECTIONS = 10
BUFFER_SIZE = 1024
BIND_IP = "0.0.0.0"  # Aceita conexões de qualquer interface

def configure_logger():
    logger = logging.getLogger('tcp_persistent_server')
    logger.setLevel(logging.INFO)
    
    # Criar arquivo de log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
    
    # Configurar handler de arquivo
    file_handler = logging.FileHandler(LOG_FILE)
    file_formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    return logger

def handle_client(client_socket, addr, logger):
    client_ip = addr[0]
    logger.info(f"Conexão estabelecida com {client_ip}")
    print(f"[+] Conexão estabelecida com {client_ip}")
    
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
                
            recv_time = time.perf_counter()
            
            try:
                send_time = float(data.decode().strip())
                latency_ms = (recv_time - send_time) * 1000
                seq = int(send_time * 1000)
                
                log_msg = f"src={client_ip} seq={seq} latency={latency_ms:.3f}ms"
                logger.info(log_msg)
                print(f"Medição: {log_msg}")
                
            except ValueError:
                logger.warning(f"Payload inválido de {client_ip}: {data.decode()}")
            except Exception as e:
                logger.error(f"Erro no processamento: {e}")
                
    except ConnectionResetError:
        logger.info(f"Conexão resetada por {client_ip}")
    except Exception as e:
        logger.error(f"Erro na conexão com {client_ip}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Conexão encerrada com {client_ip}")
        print(f"[-] Conexão encerrada com {client_ip}")

def start_server(logger):
    # Criar socket IPv4
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Habilitar reutilização de endereço
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Habilitar keepalive
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    
    try:
        # Vincular a todas as interfaces
        server_socket.bind((BIND_IP, PORT))
        server_socket.listen(MAX_CONNECTIONS)
        
        # Obter endereço real
        server_ip, server_port = server_socket.getsockname()
        logger.info(f"Servidor iniciado em {server_ip}:{PORT}")
        print(f"[+] Servidor TCP persistente iniciado em {server_ip}:{PORT}")
        print(f"[*] Logs em {LOG_FILE}")
        print(f"[*] Aguardando conexões...")
        
        while True:
            print("Aguardando nova conexão...")
            client_socket, addr = server_socket.accept()
            print(f"Recebida conexão de {addr[0]}:{addr[1]}")
            
            # Configurar timeout para recebimento
            client_socket.settimeout(10.0)
            
            Thread(
                target=handle_client,
                args=(client_socket, addr, logger),
                daemon=True
            ).start()
            
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário")
        logger.info("Servidor interrompido pelo usuário")
    except OSError as e:
        logger.error(f"Erro de SO: {e}")
        print(f"ERRO CRÍTICO: {e}")
        print("Soluções possíveis:")
        print("1. Verificar se a porta está livre: sudo lsof -i :5000")
        print("2. Esperar 30 segundos após encerrar o servidor anterior")
        print("3. Executar com privilégios: sudo python3 ...")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        print(f"ERRO FATAL: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    logger = configure_logger()
    start_server(logger)