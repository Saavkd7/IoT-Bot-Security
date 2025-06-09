#!/usr/bin/env python3

import scapy.all as scapy
import netifaces
import socket
from ipaddress import ip_network
from datetime import datetime

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
    net = ip_network(f"{ip}/{mask}", strict=False)
    return str(net)

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "unknown"

def arp_scan(ip_range, iface):
    print(f"[*] Scanning subnet: {ip_range} on interface {iface}")
    answered, _ = scapy.arping(ip_range, timeout=2, verbose=0, iface=iface)
    hosts = []
    for _, received in answered:
        hosts.append({
            "IP": received.psrc,
            "MAC": received.hwsrc,
            "Host": get_hostname(received.psrc)
        })
    return hosts

if __name__ == "__main__":
    print("🔎 IoT Recon Scanner")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    ip, mask, iface = get_local_ip_and_iface()
    if not ip:
        print("[!] No active network interface found.")
        exit(1)

    cidr_range = cidr_from_ip_and_mask(ip, mask)
    hosts = arp_scan(cidr_range, iface)

    print("\n📋 Devices Found:\n")
    print("{:<16} {:<20} {:<30}".format("IP Address", "MAC Address", "Hostname"))
    print("-" * 70)
    for host in hosts:
        print("{:<16} {:<20} {:<30}".format(host["IP"], host["MAC"], host["Host"]))

    print(f"\n✅ {len(hosts)} devices discovered.")
