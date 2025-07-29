#!/bin/bash
for PORT in 5201 5202 5203 5204 5205 5206 5207 5208 5209 5210; do
  iperf3 -s -p $PORT &
done