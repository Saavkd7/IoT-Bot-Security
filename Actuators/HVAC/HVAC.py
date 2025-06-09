# ACTUATOR: HVAC.py (HMAC-enabled HVAC logic)
import os
import json
import ssl
import time
import hmac
import hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

# ========== CONFIG ==========
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883
HMAC_SECRET = os.getenv("HMAC_SECRET", "defaultsecret").encode()

CONTROL_TOPIC = "building/zone2/ac/control"
STATE_TOPIC = "building/zone2/ac/state"
HEARTBEAT_TOPIC = "hub/heartbeat"

last_heartbeat = time.time()
current_temp = 22.0  
current_state = "idle"

# ========== UTILS ==========
def get_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M")

def sign(pkt):
    if not ENABLE_HMAC:
        return ""
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
    payload = {
        "device_id": "hvac_01",
        "state": current_state,
        "value": round(current_temp, 2),
        "timestamp": get_timestamp()
    }
    if ENABLE_HMAC:
        payload["hmac"] = sign(payload)
    client.publish(STATE_TOPIC, json.dumps(payload))
    print(f"[HVAC]  State: {current_state.upper()} | Room: {round(current_temp, 2)}°C")

# ========== MQTT CALLBACKS ==========
def on_connect(client, userdata, flags, rc):
    print("[HVAC]  Connected to MQTT broker.")
    client.subscribe(CONTROL_TOPIC)
    client.subscribe(HEARTBEAT_TOPIC)

def on_disconnect(client, userdata, rc):
    print("[HVAC]  Disconnected from broker.")

def on_message(client, userdata, msg):
    global last_heartbeat, current_temp, current_state
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()
    elif msg.topic == CONTROL_TOPIC:
        try:
            data = json.loads(msg.payload.decode())
            if not verify(data):
                print("[HVAC]  Invalid HMAC — rejected.")
                return

            new_temp = data.get("value")
            if new_temp is not None:
                current_temp = new_temp
                print(f"[HVAC]  Sensor reports: {current_temp}°C")

                new_state = current_state
                if current_temp < 20.0:
                    new_state = "heating"
                elif current_temp > 24.0:
                    new_state = "cooling"
                else:
                    new_state = "idle"

                if new_state != current_state:
                    current_state = new_state
                    publish_state(client)
        except Exception as e:
            print(f"[HVAC]  Error: {e}")

# ========== MQTT SETUP ==========
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(1, 30)

# ========== CONNECT LOOP ==========
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[HVAC]  Retry connection: {e}")
        time.sleep(3)

client.loop_start()
print("[HVAC]  Waiting for room temperature readings...")

# ========== MAIN LOOP ==========
while True:
    if time.time() - last_heartbeat > 15:
        print("[HVAC]  Paused (hub heartbeat missing)")
    time.sleep(5)

