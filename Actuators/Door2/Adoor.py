import os
import json
import ssl
import time
import hmac
import hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883

CONTROL_TOPIC = "building/zone1/door/lock"
STATE_TOPIC = "building/zone1/door/state"
HEARTBEAT_TOPIC = "hub/heartbeat"
HMAC_SECRET = os.getenv("HMAC_SECRET", "defaultsecret").encode()
DEVICE_ID = "door_lock_01"
last_heartbeat = time.time()
door_state = "locked"

def get_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M")

def sign(pkt):
    raw = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(',', ':'), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, raw, hashlib.sha256).hexdigest()

def verify(pkt):
    if not ENABLE_HMAC:
        return True
    sig = pkt.get("hmac")
    data = {k: pkt[k] for k in sorted(pkt) if k != "hmac"}
    calc = hmac.new(HMAC_SECRET, json.dumps(data, separators=(',', ':'), sort_keys=True).encode(), hashlib.sha256).hexdigest()
    return sig and hmac.compare_digest(calc, sig)

def publish_state(client):
    msg = {"device_id": DEVICE_ID, "state": door_state, "timestamp": get_timestamp()}
    msg["hmac"] = sign(msg)
    client.publish(STATE_TOPIC, json.dumps(msg))
    print(f"[DOOR]  State: {door_state.upper()}")

def on_connect(client, userdata, flags, rc):
    print("[DOOR]  Connected.")
    client.subscribe(CONTROL_TOPIC)
    client.subscribe(HEARTBEAT_TOPIC)

def on_message(client, userdata, msg):
    global last_heartbeat, door_state
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()
    elif msg.topic == CONTROL_TOPIC:
        try:
            data = json.loads(msg.payload.decode())
            if not verify(data):
                print("[DOOR]  Invalid HMAC — ignored.")
                return
            action = data.get("action")
            if action == "unlock" and door_state != "unlocked":
                door_state = "unlocked"
                print("[DOOR]  Unlocking.")
                publish_state(client)
            elif action == "lock" and door_state != "locked":
                door_state = "locked"
                print("[DOOR]  Locking.")
                publish_state(client)
        except Exception as e:
            print(f"[DOOR]  {e}")

client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, port=PORT)
client.loop_start()
print("[DOOR] Awaiting commands...")
while True:
    if time.time() - last_heartbeat > 15:
        print("[DOOR]  Paused (hub heartbeat missing)")
    time.sleep(5)
