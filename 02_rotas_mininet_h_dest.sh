#!/bin/bash
# Adicionar rotas para redes Mininet
ip route add 172.16.2.0/24 via 10.0.1.1 dev eth1
ip route add 172.16.3.0/24 via 10.0.1.1 dev eth1
ip route add 172.16.4.0/24 via 10.0.1.1 dev eth1
ip route add 172.16.5.0/24 via 10.0.1.1 dev eth1
ip route add 192.168.7.0/24 via 10.0.1.1 dev eth1
ip route add 192.168.8.0/24 via 10.0.1.1 dev eth1