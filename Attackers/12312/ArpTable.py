import os
import subprocess
from scapy.all import *
from scapy.layers.l2 import ARP, Ether

INTERFACE = "eth1"
SUBNET = "192.168.10.0/24"

def ping_sweep(subnet):
    print(f"[*] Pinging devices to populate ARP table...")
    for i in range(1, 255):
        os.system(f"ping -c 1 -W 1 192.168.10.{i} > /dev/null 2>&1")

def get_arp_table():
    print("[*] Reading ARP table...")
    result = subprocess.check_output("arp -n", shell=True).decode()
    victims = []
    for line in result.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3 and parts[2] != "<incomplete>":
            victims.append((parts[0], parts[2]))
    return victims

if __name__ == "__main__":
    ping_sweep(SUBNET)
    victims = get_arp_table()
    if victims:
        print("[+] Found victims:")
        for ip, mac in victims:
            print(f"    {ip} → {mac}")
    else:
        print("[-] No victims found.")

