# IFPB_Projeto_Redes
Lista completa de requisitos para executar o cenário em uma máquina virtual Ubuntu:
________________________________________
1. Requisitos de Sistema
•	Sistema Operacional: Ubuntu 22.04 LTS (ou superior)
•	Kernel: Linux 5.15+ (suporte a namespaces/networking)
•	Recursos Mínimos:
o	CPU: 4 núcleos
o	RAM: 8 GB
o	Armazenamento: 20 GB (SSD recomendado)
o	Acesso root/sudo para operações privilegiadas
________________________________________
2. Dependências de Pacotes
bash
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
________________________________________
3. Configuração do Docker
bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Iniciar serviço Docker
sudo systemctl enable docker && sudo systemctl start docker
________________________________________
4. Dependências Python
bash
# Instalar bibliotecas Python
pip3 install \
  scapy \
  paramiko \
  mininet \
  psutil \
  numpy
________________________________________
5. Configuração Específica do Projeto
1.	Estrutura de Diretórios:
bash
mkdir -p ~/projeto_final/{scripts,logs,configs}
o	Todos os scripts devem ser copiados para ~/projeto_final/scripts/
o	Arquivos de log em ~/projeto_final/logs/
2.	Permissões de Execução:
bash
chmod +x ~/projeto_final/scripts/*.sh
chmod +x ~/projeto_final/scripts/*.py
________________________________________
6. Configurações de Rede
•	Habilitar IP Forwarding:
bash
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
•	Desativar Firewall/Conflitos:
bash
sudo systemctl stop ufw && sudo systemctl disable ufw
________________________________________
7. Configuração do Ambiente Mininet
1.	Instalar Mininet:
bash
git clone https://github.com/mininet/mininet
cd mininet
sudo util/install.sh -nfvp
2.	Validar Instalação:
bash
sudo mn --test pingall
________________________________________
8. Pré-requisitos para QoS
•	HTB/PFIFO: Suporte do kernel para QoS:
bash
sudo apt install -y linux-tools-common linux-tools-generic
•	Módulos do Kernel:
bash
sudo modprobe sch_htb sch_prio sch_netem
________________________________________
9. Configuração do Container Docker (h_dest)
Execute sequencialmente:
bash
cd ~/projeto_final/scripts/
./01_DockerSetup_h_dest.sh start
./01_DockerSetup_h_dest.sh install
________________________________________
10. Serviços Adicionais
•	SSH nos Roteadores: Credenciais padrão (mininet:m1ninetpwd)
•	Servidor Iperf (no container):
bash
docker exec -d h_dest_container /app/07_start_iperf3_servers.sh
________________________________________
11. Fluxo de Execução Típico
1.	Iniciar Topologia Mininet:
bash
sudo python3 ~/projeto_final/scripts/03_InfraMininet_HTB.py --bw 100 --delay 1 --loss 0
2.	Gerar Tráfego:
o	uRLLC (dentro do Mininet):
bash
mininet> h3_urllc python3 /caminho/04_TCP_uRLLC_trafego_SOCKET.py --server 10.0.1.2
o	eMBB:
bash
./05_UDP_eMBB_trafego.sh
3.	Monitorar QoS:
bash
python3 ~/projeto_final/scripts/qos_controller_htb.py
________________________________________
12. Validação Pós-Instalação
•	Verifique interfaces Docker:
bash
brctl show docker-br
•	Teste conectividade do container:
bash
docker exec h_dest_container ping 10.0.1.1
•	Verifique rotas no container:
bash
docker exec h_dest_container ip route
________________________________________
Notas Importantes
1.	Todos os comandos sudo exigem senha do usuário.
2.	Scripts .sh devem ser executados no diretório do projeto.
3.	Para topologias alternativas (sem QoS):
bash
sudo python3 03_InfraMininet_noQOS.py --bw 100
4.	Logs detalhados estão em:
o	/var/log/tcp_persistent_server.log
o	/var/log/urllc_tcp_window_stats.log
Este checklist cobre todos os requisitos técnicos para replicar o ambiente descrito nos scripts. Recomenda-se uma VM dedicada para evitar conflitos de configuração.


