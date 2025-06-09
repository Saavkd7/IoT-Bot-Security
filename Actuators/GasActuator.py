# ACTUATOR: GasActuator.py (Final Version — 3-State with Feedback)
import os, json, ssl, time
import paho.mqtt.client as mqtt
from datetime import datetime

# === CONFIG ===
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883

CONTROL_TOPIC = "building/zone3/alarm/control"
STATE_TOPIC = "building/zone3/alarm/state"
HEARTBEAT_TOPIC = "hub/heartbeat"

last_heartbeat = time.time()
alarm_state = "normal"

# === HELPERS ===
def get_timestamp():
    return datetime.now().strftime("%d/%m/%y %H:%M")

def simulate_audio_feedback(state):
    if state == "warning":
        print("[AUDIO] 📢 Gas detected! Open windows and stay alert.")
    elif state == "danger":
        print("[SIREN] 🚨 DANGER! Evacuate immediately!")
    elif state == "normal":
        print("[GAS ALARM] ✅ Air quality normal.")

def publish_state(client):
    payload = {
        "actuator": "Gas Alarm",
        "state": alarm_state,
        "timestamp": get_timestamp()
    }
    client.publish(STATE_TOPIC, json.dumps(payload))
    simulate_audio_feedback(alarm_state)

# === CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    print("[GAS ALARM] ✅ Connected to MQTT broker.")
    client.subscribe(CONTROL_TOPIC)
    client.subscribe(HEARTBEAT_TOPIC)

def on_disconnect(client, userdata, rc):
    print("[GAS ALARM] 🔌 Disconnected.")

def on_message(client, userdata, msg):
    global last_heartbeat, alarm_state
    if msg.topic == HEARTBEAT_TOPIC:
        last_heartbeat = time.time()
    elif msg.topic == CONTROL_TOPIC:
        try:
            data = json.loads(msg.payload.decode())
            new_state = data.get("state", "normal").lower()
            if new_state != alarm_state and new_state in ["normal", "warning", "danger"]:
                alarm_state = new_state
                print(f"[GAS ALARM] 🔔 State → {alarm_state.upper()}")
                publish_state(client)
        except Exception as e:
            print(f"[GAS ALARM] ❌ Error: {e}")

# === MQTT SETUP ===
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set("/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(1, 30)

# === CONNECT & MAIN LOOP ===
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[GAS ALARM] 🔁 Retrying: {e}")
        time.sleep(3)

client.loop_start()
print("[GAS ALARM] 🔄 Listening for gas alarm states...")

while True:
    if time.time() - last_heartbeat > 15:
        print("[GAS ALARM] ⏸ Paused (hub heartbeat missing)")
    time.sleep(5)

