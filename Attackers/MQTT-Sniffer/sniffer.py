from scapy.all import sniff, Raw
import binascii

def process_packet(packet):
    if packet.haslayer(Raw):
        payload = packet[Raw].load
        if b'\x10' in payload[:1]:  # MQTT CONNECT packet type
            print("\n[🔓] MQTT CONNECT Packet Captured")
            try:
                printable = payload.decode(errors='ignore')
                print("[🧠] Decoded Payload:", printable)
            except Exception as e:
                print(f"[!] Decode error: {e}")

sniff(iface="eth0", filter="tcp port 1883", prn=process_packet, store=0)
