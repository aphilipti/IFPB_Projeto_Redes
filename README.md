# Cenário de Rede com Mininet e QoS

Este documento descreve os requisitos e procedimentos para configurar um ambiente de rede com suporte a QoS (Quality of Service) usando Mininet e Docker em uma máquina Ubuntu.

## 📋 Requisitos de Sistema
- **Sistema Operacional**: Ubuntu 22.04 LTS (ou superior)
- **Kernel Linux**: 5.15+ (com suporte a namespaces/networking)
- **Recursos Mínimos**:
  - CPU: 4 núcleos
  - RAM: 8 GB
  - Armazenamento: 20 GB (SSD recomendado)
- Acesso `root/sudo` obrigatório para operações privilegiadas

## ⚙️ Instalação e Configuração

### 1. Dependências de Pacotes
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências essenciais
sudo apt install -y \
  docker.io \
  openvswitch-switch \
  bridge-utils \
  net-tools \
  iproute2 \
  iperf3 \
  tcpdump \
  python3 \
  python3-pip \
  git \
  build-essential \
  libssl-dev \
  ethtool
```

### 2. Configuração do Docker
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Iniciar serviço Docker
sudo systemctl enable docker && sudo systemctl start docker
```

### 3. Dependências Python
```bash
pip3 install \
  scapy \
  paramiko \
  mininet \
  psutil \
  numpy
```

### 4. Configuração do Projeto
```bash
# Criar estrutura de diretórios
mkdir -p ~/projeto_final/{scripts,logs,configs}

# Dar permissão de execução aos scripts
chmod +x ~/projeto_final/scripts/*.sh
chmod +x ~/projeto_final/scripts/*.py
```

### 5. Configurações de Rede
```bash
# Habilitar IP Forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Desativar firewall
sudo systemctl stop ufw && sudo systemctl disable ufw
```

### 6. Ambiente Mininet
```bash
# Instalar Mininet
git clone https://github.com/mininet/mininet
cd mininet
sudo util/install.sh -nfvp

# Validar instalação
sudo mn --test pingall
```

### 7. Pré-requisitos para QoS
```bash
# Instalar ferramentas
sudo apt install -y linux-tools-common linux-tools-generic

# Carregar módulos do kernel
sudo modprobe sch_htb sch_prio sch_netem
```

## 🚀 Fluxo de Execução

### 1. Configurar Container Docker (h_dest)
```bash
cd ~/projeto_final/scripts/
./01_DockerSetup_h_dest.sh start
./01_DockerSetup_h_dest.sh install
```

### 2. Iniciar Serviços Adicionais
```bash
# Iniciar servidor Iperf no container
docker exec -d h_dest_container /app/07_start_iperf3_servers.sh
```

### 3. Executar Cenário Principal
```bash
# Iniciar topologia Mininet com QoS
sudo python3 ~/projeto_final/scripts/03_InfraMininet_HTB.py --bw 100 --delay 1 --loss 0

# Dentro do ambiente Mininet:
mininet> h3_urllc python3 /caminho/04_TCP_uRLLC_trafego_SOCKET.py --server 10.0.1.2

# Em outro terminal:
./05_UDP_eMBB_trafego.sh

# Monitorar QoS
python3 ~/projeto_final/scripts/qos_controller_htb.py
```

### 4. Topologia Alternativa (sem QoS)
```bash
sudo python3 03_InfraMininet_noQOS.py --bw 100
```

## ✔️ Validação Pós-Instalação
```bash
# Verificar interfaces Docker
brctl show docker-br

# Testar conectividade do container
docker exec h_dest_container ping 10.0.1.1

# Verificar rotas no container
docker exec h_dest_container ip route
```

## 📝 Notas Importantes
1. Todos os comandos `sudo` exigem a senha do usuário
2. Scripts `.sh` devem ser executados no diretório do projeto
3. Credenciais padrão SSH para roteadores: 
   - Usuário: `mininet`
   - Senha: `m1ninetpwd`
4. Logs principais:
   - `/var/log/tcp_persistent_server.log`
   - `/var/log/urllc_tcp_window_stats.log`
5. Recomenda-se usar uma VM dedicada para evitar conflitos de configuração

## 🔍 Informações Adicionais
Para suporte ou problemas, consulte a documentação oficial do [Mininet](http://mininet.org/) e [Docker](https://docs.docker.com/).
