#!/bin/sh

# Wait for eth1 to be fully up
sleep 3

echo "[*] Enabling promiscuous mode on eth1..."
ip link set eth0 promisc on
ip link set eth1 promisc on

# Confirm and log
ip link show eth0 | grep PROMISC || echo "[-] PROMISC not active."
ip link show eth1 | grep PROMISC || echo "[-] PROMISC not active."


# Keep container alive
exec bash

