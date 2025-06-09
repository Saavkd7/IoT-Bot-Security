#!/usr/bin/env python3

from scapy.all import ARP, arping
import netifaces
import socket
import time
from ipaddress import ip_network

# === CONFIGURATION ===
interface = "eth0"
mqtt_ports = [1883, 8883]
scan_timeout = 2

# === GET LOCAL INFO ===
def get_local_ip_and_iface():
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ipv4 = addrs[netifaces.AF_INET][0]
            ip = ipv4['addr']
            mask = ipv4['netmask']
            if ip != "127.0.0.1":
                return ip, mask, iface
    return None, None, None

def cidr_from_ip_and_mask(ip, mask):
    return str(ip_network(f"{ip}/{mask}", strict=False))

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unknown"

def is_mqtt(ip, port):
    try:
        s = socket.create_connection((ip, port), timeout=1)
        s.close()
        return True
    except:
        return False

# === MAIN ===
print("🔎 Full IoT Recon: Devices + MQTT Brokers")
ip, mask, iface = get_local_ip_and_iface()
if not ip:
    print("[!] Could not detect active interface.")
    exit(1)

cidr_range = cidr_from_ip_and_mask(ip, mask)
print(f"[*] Scanning subnet {cidr_range} on interface {iface}...")

# ARP Scan
answered, _ = arping(cidr_range, timeout=scan_timeout, verbose=0, iface=iface)
hosts = []
for _, received in answered:
    ip_addr = received.psrc
    mac_addr = received.hwsrc
    host = {
        "ip": ip_addr,
        "mac": mac_addr,
        "hostname": get_hostname(ip_addr),
        "is_mqtt": False,
        "tls_mqtt": False
    }
    # Check for MQTT broker
    if is_mqtt(ip_addr, 1883):
        host["is_mqtt"] = True
    elif is_mqtt(ip_addr, 8883):
        host["tls_mqtt"] = True
    hosts.append(host)

# Display Results
print("\n📋 Devices Discovered:")
print("{:<16} {:<20} {:<30} {:<10} {:<10}".format("IP", "MAC", "Hostname", "MQTT", "TLS"))
print("-" * 90)
for h in hosts:
    print("{:<16} {:<20} {:<30} {:<10} {:<10}".format(
        h["ip"], h["mac"], h["hostname"],
        "✅" if h["is_mqtt"] else "", "🔒" if h["tls_mqtt"] else ""
    ))

print(f"\n✅ Scan complete. {len(hosts)} total devices.")
mqtt_found = [h for h in hosts if h["is_mqtt"] or h["tls_mqtt"]]
if mqtt_found:
    print(f"🚀 MQTT Broker candidates found:")
    for b in mqtt_found:
        print(f" - {b['ip']} (TLS: {'Yes' if b['tls_mqtt'] else 'No'})")
else:
    print("❌ No MQTT brokers detected.")
