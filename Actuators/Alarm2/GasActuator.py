#!/usr/bin/env python3
# ACTUATOR: alarm.py (Gas alarm actuator with HMAC + heartbeat)

import os
import json
import ssl
import time
import hmac
import hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────────────────
BROKER        = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT          = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME      = os.getenv("MQTT_USERNAME", "")
PASSWORD      = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS    = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH   = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC   = os.getenv("ENABLE_HMAC", "true" ).lower() == "true"
HMAC_SECRET   = os.getenv("HMAC_SECRET", "123iot45").encode()

DEVICE_ID     = "alarm_gas_01"
CTRL_TOPIC    = "building/zone3/alarm/control"
STATE_TOPIC   = "building/zone3/alarm/state"
HEARTBEAT     = "hub/heartbeat"

alarm_state   = "idle"
last_hb       = time.time()

# ─── UTILS ─────────────────────────────────────────────────────────────
def now_str():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def sign(pkt):
    if not ENABLE_HMAC:
        return ""
    raw = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(",", ":"), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, raw, hashlib.sha256).hexdigest()

def verify(pkt):
    if not ENABLE_HMAC:
        return True
    sig = pkt.get("hmac")
    data = {k: pkt[k] for k in sorted(pkt) if k != "hmac"}
    calc = hmac.new(HMAC_SECRET, json.dumps(data, separators=(",", ":"), sort_keys=True).encode(), hashlib.sha256).hexdigest()
    return sig and hmac.compare_digest(calc, sig)

def publish_state(client):
    payload = {
        "device_id": DEVICE_ID,
        "state": alarm_state,
        "timestamp": now_str()
    }
    if ENABLE_HMAC:
        payload["hmac"] = sign(payload)
    client.publish(STATE_TOPIC, json.dumps(payload))
    print(f"[ALARM]  State: {alarm_state.upper()}")

# ─── MQTT CALLBACKS ─────────────────────────────────────────────────────
def on_connect(client, *_):
    print("[ALARM]  Connected to MQTT broker.")
    client.subscribe(CTRL_TOPIC)
    client.subscribe(HEARTBEAT)

def on_disconnect(client, *_):
    print("[ALARM]  Disconnected from broker.")

def on_message(client, userdata, msg):
    global alarm_state, last_hb

    if msg.topic == HEARTBEAT:
        last_hb = time.time()
        return

    if msg.topic == CTRL_TOPIC:
        try:
            data = json.loads(msg.payload.decode())
            if not verify(data):
                print("[ALARM]  Invalid HMAC — message ignored.")
                return

            action = data.get("state")
            if action and action != alarm_state:
                alarm_state = action
                print(f"[ALARM]  ALARM {alarm_state.upper()} TRIGGERED")
                publish_state(client)

        except Exception as e:
            print(f"[ALARM]  Error processing command: {e}")

# ─── CLIENT SETUP ───────────────────────────────────────────────────────
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set("/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect    = on_connect
client.on_disconnect = on_disconnect
client.on_message    = on_message
client.reconnect_delay_set(1, 30)

# ─── CONNECT LOOP ───────────────────────────────────────────────────────
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[ALARM]  Reconnecting: {e}")
        time.sleep(3)

client.loop_start()
print("[ALARM]  Waiting for gas control commands...")

# ─── MAIN LOOP ──────────────────────────────────────────────────────────
while True:
    if time.time() - last_hb > 15:
        print("[ALARM] Paused (no heartbeat from hub)")
    time.sleep(5)

