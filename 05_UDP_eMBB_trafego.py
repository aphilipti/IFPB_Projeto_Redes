#!/usr/bin/env python3
import time, random
from scapy.all import *
while True:
    try:
        p = IP(dst="10.0.1.2", tos=0xB8)/UDP(dport=5000)/Raw(load=str(time.perf_counter()))
        send(p, verbose=0)
        time.sleep(0.5)
    except:
        time.sleep(1)