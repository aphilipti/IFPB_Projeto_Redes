#!/bin/bash
# Script revisado usando abordagem de rede Docker personalizada

ACTION=${1:-start}
CONTAINER_NAME="h_dest_container"
BRIDGE_NAME="docker-br"
NETWORK_NAME="mininet-net"
SUBNET="10.0.1.0/24"
GATEWAY="10.0.1.1"
CONTAINER_IP="10.0.1.2"

# Lista de redes Mininet
MININET_NETWORKS=(
    "172.16.2.0/24"
    "172.16.3.0/24"
    "172.16.4.0/24"
    "172.16.5.0/24"
    "192.168.7.0/24"
    "192.168.8.0/24"
)

case $ACTION in
    start)
        # Verificar se container já existe
        if docker ps -a | grep -q "$CONTAINER_NAME"; then
            echo "Container já existe. Use '$0 stop' primeiro."
            exit 1
        fi

        # 1. Criar rede Docker personalizada se não existir
        if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
            echo "Criando rede Docker $NETWORK_NAME..."
            docker network create \
                --driver bridge \
                --subnet "$SUBNET" \
                --opt "com.docker.network.bridge.name=$BRIDGE_NAME" \
                "$NETWORK_NAME"
        fi

        # 2. Criar container com acesso à internet e rede Mininet
        docker run -d --name "$CONTAINER_NAME" \
            --network bridge \
            --cap-add NET_ADMIN \
            -v "$(pwd)/scripts:/app" \
            ubuntu:22.04 \
            /bin/bash -c 'tail -f /dev/null'
        
        # 3. Conectar container à rede Mininet
        docker network connect \
            --ip "$CONTAINER_IP" \
            "$NETWORK_NAME" \
            "$CONTAINER_NAME"
        
        echo "Container criado e conectado às redes."
        echo "Execute '$0 install' para instalar dependências"
        ;;
    
    install)
        # Verificar se container está rodando
        if ! docker ps | grep -q "$CONTAINER_NAME"; then
            echo "ERRO: Container não está rodando. Execute '$0 start' primeiro."
            exit 1
        fi
        
        # Instalar dependências necessárias
        docker exec "$CONTAINER_NAME" apt-get update
        docker exec "$CONTAINER_NAME" apt-get install -y \
            python3 \
            iproute2 \
            net-tools \
            iputils-ping \
            tcpdump \
            iperf3
        
        # Adicionar rotas para redes Mininet
        for network in "${MININET_NETWORKS[@]}"; do
            docker exec "$CONTAINER_NAME" ip route add "$network" via "$GATEWAY"
            echo "Rota adicionada: $network via $GATEWAY"
        done
        
        echo "Dependências instaladas e rotas configuradas."
        echo "Agora você pode iniciar a topologia Mininet"
        ;;
        
    shell)
        docker exec -it "$CONTAINER_NAME" /bin/bash
        ;;
        
    stop)
        # Desconectar da rede Mininet
        docker network disconnect "$NETWORK_NAME" "$CONTAINER_NAME" 2>/dev/null
        
        # Parar e remover container
        docker stop "$CONTAINER_NAME" 2>/dev/null
        docker rm "$CONTAINER_NAME" 2>/dev/null
        
        # Opcional: remover rede Docker
        # docker network rm "$NETWORK_NAME" 2>/dev/null
        
        echo "Container removido"
        ;;
        
    *)
        echo "Uso: $0 [start|install|shell|stop]"
        echo "  start   : Cria container e conecta às redes"
        echo "  install : Instala dependências e configura rotas"
        echo "  shell   : Acesso interativo ao container"
        echo "  stop    : Remove container"
        exit 1
        ;;
esac