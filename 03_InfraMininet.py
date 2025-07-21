#!/usr/bin/env python3
"""
Topologia Mininet com integração Docker - Versão 5
"""
import argparse
import os
import time
from mininet.net import Mininet
from mininet.node import Node, OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info, error
from mininet.cli import CLI

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        info(f'*** Habilitando ip_forward em {self.name}\n')
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
    
    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()

def configure_qos(router, intf):
    """Configura QoS com r2q para evitar warnings"""
    info(f'*** Configurando QoS em {router.name} interface {intf}\n')
    router.cmd(f'tc qdisc del dev {intf} root 2>/dev/null || true')
    router.cmd(f'tc qdisc add dev {intf} root handle 1: prio bands 3 r2q 10')
    router.cmd(f'tc filter add dev {intf} parent 1: protocol ip prio 1 u32 match ip tos 0xb8 0xff flowid 1:1')
    router.cmd(f'tc filter add dev {intf} parent 1: protocol ip prio 2 u32 match ip tos 0x28 0xff flowid 1:2')
    router.cmd(f'tc qdisc add dev {intf} parent 1:1 handle 10: pfifo limit 1000')
    router.cmd(f'tc qdisc add dev {intf} parent 1:2 handle 20: pfifo limit 5000')
    router.cmd(f'tc qdisc add dev {intf} parent 1:3 handle 30: pfifo limit 10000')

def verify_docker_bridge(bridge_name):
    """Verifica se a bridge Docker existe"""
    if os.system(f'sudo brctl show {bridge_name} >/dev/null 2>&1') != 0:
        error(f'*** ERRO: Bridge {bridge_name} não encontrada! Execute o setup_h_dest_containerV5.sh primeiro.\n')
        exit(1)
    else:
        info(f'*** Utilizando bridge existente: {bridge_name}\n')

def connect_bridge_to_switch(switch, bridge_name):
    """Conecta bridge Docker ao switch Mininet"""
    info(f'*** Conectando bridge {bridge_name} ao switch {switch}\n')
    
    # Criar par veth
    veth_host = f'veth-{switch}'
    veth_switch = f'veth-{switch}-switch'
    os.system(f'sudo ip link add {veth_host} type veth peer name {veth_switch} >/dev/null 2>&1')
    
    # Conectar à bridge Docker
    os.system(f'sudo brctl addif {bridge_name} {veth_host} >/dev/null 2>&1')
    os.system(f'sudo ip link set {veth_host} up >/dev/null 2>&1')
    
    # Conectar ao switch OVS
    os.system(f'sudo ovs-vsctl add-port {switch} {veth_switch} >/dev/null 2>&1')
    os.system(f'sudo ip link set {veth_switch} up >/dev/null 2>&1')
    
    return (veth_host, veth_switch)

def build_net(bw, delay, loss):
    BRIDGE_NAME = "docker-br"  # Nome da bridge Docker
    
    net = Mininet(link=TCLink, switch=OVSSwitch)
    
    # Verificar se a bridge Docker existe
    verify_docker_bridge(BRIDGE_NAME)
    
    info('*** Criando roteadores\n')
    r1 = net.addHost('r1', cls=LinuxRouter, ip=None)
    r2 = net.addHost('r2', cls=LinuxRouter, ip=None)
    r3 = net.addHost('r3', cls=LinuxRouter, ip=None)
    r4 = net.addHost('r4', cls=LinuxRouter, ip=None)
    
    info('*** Criando switches\n')
    s1 = net.addSwitch('s1')  # Switch entre R1 e Docker
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    
    info('*** Criando hosts\n')
    # Hosts uRLLC e eMBB (não inclui h_dest)
    h3_urllc = net.addHost('h3_urllc', ip='192.168.7.2/24', defaultRoute='via 192.168.7.1')
    h3_embb = net.addHost('h3_embb', ip='192.168.7.3/24', defaultRoute='via 192.168.7.1')
    h4_urllc = net.addHost('h4_urllc', ip='192.168.8.2/24', defaultRoute='via 192.168.8.1')
    h4_embb = net.addHost('h4_embb', ip='192.168.8.3/24', defaultRoute='via 192.168.8.1')

    # Conexões entre roteadores e switches
    info('*** Criando links entre roteadores\n')
    net.addLink(r1, r2, 
                intfName1='r1-eth2', intfName2='r2-eth1',
                params1={'ip': '172.16.2.1/24'}, 
                params2={'ip': '172.16.2.2/24'},
                cls=TCLink, bw=bw, delay=f'{delay}ms', loss=loss)
    
    net.addLink(r2, r3, 
                intfName1='r2-eth2', intfName2='r3-eth1',
                params1={'ip': '172.16.3.1/24'}, 
                params2={'ip': '172.16.3.2/24'},
                cls=TCLink, bw=bw, delay=f'{delay}ms', loss=loss)
    
    net.addLink(r2, r4, 
                intfName1='r2-eth3', intfName2='r4-eth1',
                params1={'ip': '172.16.4.1/24'}, 
                params2={'ip': '172.16.4.2/24'},
                cls=TCLink, bw=bw, delay=f'{delay}ms', loss=loss)
    
    net.addLink(r3, r4, 
                intfName1='r3-eth2', intfName2='r4-eth2',
                params1={'ip': '172.16.5.1/24'}, 
                params2={'ip': '172.16.5.2/24'},
                cls=TCLink, bw=bw, delay=f'{delay}ms', loss=loss)
    
    info('*** Criando links com switches\n')
    net.addLink(r1, s1, 
                intfName1='r1-eth1',
                params1={'ip': '10.0.1.1/24'})
    
    net.addLink(r3, s3, 
                intfName1='r3-eth3',
                params1={'ip': '192.168.7.1/24'})
    net.addLink(s3, h3_urllc)
    net.addLink(s3, h3_embb)
    
    net.addLink(r4, s4, 
                intfName1='r4-eth3',
                params1={'ip': '192.168.8.1/24'})
    net.addLink(s4, h4_urllc)
    net.addLink(s4, h4_embb)
    
    info('*** Iniciando rede\n')
    net.start()
    
    # Configurar switches
    info('*** Configurando switches\n')
    s1.cmd('ovs-ofctl add-flow s1 actions=NORMAL')
    s3.cmd('ovs-ofctl add-flow s3 actions=NORMAL')
    s4.cmd('ovs-ofctl add-flow s4 actions=NORMAL')
    
    # Conectar bridge Docker ao switch s1
    veth_pair = connect_bridge_to_switch('s1', BRIDGE_NAME)
    
    info('*** Configurando rotas estáticas\n')
    # R1 (Core)
    r1.cmd('ip route add 172.16.3.0/24 via 172.16.2.2')
    r1.cmd('ip route add 172.16.4.0/24 via 172.16.2.2')
    r1.cmd('ip route add 172.16.5.0/24 via 172.16.2.2')
    r1.cmd('ip route add 192.168.7.0/24 via 172.16.2.2')
    r1.cmd('ip route add 192.168.8.0/24 via 172.16.2.2')
    
    # R2
    r2.cmd('ip route add 10.0.1.0/24 via 172.16.2.1')
    r2.cmd('ip route add 172.16.5.0/24 via 172.16.3.2')  # Via R3
    r2.cmd('ip route add 192.168.7.0/24 via 172.16.3.2')
    r2.cmd('ip route add 192.168.8.0/24 via 172.16.4.2')
    
    # R3
    r3.cmd('ip route add 10.0.1.0/24 via 172.16.3.1')    # Via R2
    r3.cmd('ip route add 172.16.2.0/24 via 172.16.3.1')
    r3.cmd('ip route add 172.16.4.0/24 via 172.16.5.2')   # Via R4 (redundância)
    r3.cmd('ip route add 192.168.8.0/24 via 172.16.5.2')  # Via R4 (redundância)
    
    # R4
    r4.cmd('ip route add 10.0.1.0/24 via 172.16.4.1')     # Via R2
    r4.cmd('ip route add 172.16.2.0/24 via 172.16.4.1')
    r4.cmd('ip route add 172.16.3.0/24 via 172.16.5.1')   # Via R3 (redundância)
    r4.cmd('ip route add 192.168.7.0/24 via 172.16.5.1')  # Via R3 (redundância)
    
    info('*** Configurando QoS em todas as interfaces\n')
    for router in [r1, r2, r3, r4]:
        for intf in router.intfNames():
            if 'eth' in intf:
                configure_qos(router, intf)
    
    info('*** Configuração de rede completa.\n')
    info('*** Container Docker deve estar conectado à bridge\n')
    info('*** Instruções para teste:\n')
    info('1. Acesse o container: ./setup_h_dest_containerV5.sh shell\n')
    info('2. Teste conectividade: ping 10.0.1.1\n')
    info('3. Teste rotas: ping 192.168.7.2\n')
    
    CLI(net)
    
    # Limpeza de rede
    info('*** Removendo recursos de rede\n')
    veth_host, veth_switch = veth_pair
    os.system(f'sudo ip link set {veth_switch} down 2>/dev/null')
    os.system(f'sudo ovs-vsctl del-port s1 {veth_switch} 2>/dev/null')
    os.system(f'sudo ip link set {veth_host} down 2>/dev/null')
    os.system(f'sudo ip link del {veth_host} 2>/dev/null')
    
    # Não removemos a bridge docker-br (gerenciada pelo Docker)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    parser = argparse.ArgumentParser(description='Topologia Mininet com bridge Docker')
    parser.add_argument('--bw', type=int, default=100, help='Largura de banda em Mbps')
    parser.add_argument('--delay', type=int, default=1, help='Atraso em ms')
    parser.add_argument('--loss', type=float, default=0, help='Perda de pacotes em porcentagem')
    args = parser.parse_args()
    build_net(args.bw, args.delay, args.loss)