# ACTUATOR: Adoor.py (Smart Door Lock Actuator)
import os
import json
import ssl
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# ========== CONFIG ==========
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883

CONTROL_TOPIC = "building/zone1/door/lock"
STATE_TOPIC = "building/zone1/door/state"
HEARTBEAT_TOPIC = "hub/heartbeat"

last_heartbeat = time.time()
door_state = "locked"

# ========== UTILS ==========
def get_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M")

def publish_state(client):
    payload = {
        "actuator": "Door Lock",
        "state": door_state,
        "timestamp": get_timestamp()
    }
    client.publish(STATE_TOPIC, json.dumps(payload))
    print(f"[DOOR] 🔐 State: {door_state.upper()}")

# ========== MQTT CALLBACKS ==========
def on_connect(client, userdata, flags, rc):
    print("[DOOR] ✅ Connected to MQTT broker.")
    client.subscribe(CONTROL_TOPIC)
    client.subscribe(HEARTBEAT_TOPIC)

def on_disconnect(client, userdata, rc):
    print("[DOOR] 🔌 Disconnected from broker.")

def on_message(client, userdata, msg):
    global last_heartbeat, door_state
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()

    elif msg.topic == CONTROL_TOPIC:
        try:
            data = json.loads(msg.payload.decode())
            action = data.get("action")

            if action == "unlock" and door_state != "unlocked":
                door_state = "unlocked"
                print("[DOOR] 🚪 Motion detected → UNLOCKING door.")
                publish_state(client)

            elif action == "lock" and door_state != "locked":
                door_state = "locked"
                print("[DOOR] 🛑 No motion → LOCKING door.")
                publish_state(client)

        except Exception as e:
            print(f"[DOOR] ❌ Error processing control message: {e}")

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
        print(f"[DOOR] 🔁 Retry connection: {e}")
        time.sleep(3)

client.loop_start()
print("[DOOR] 🔄 Awaiting motion control signals...")

# ========== MAIN LOOP ==========
while True:
    if time.time() - last_heartbeat > 15:
        print("[DOOR] ⏸ Paused (hub heartbeat missing)")
    time.sleep(5)

