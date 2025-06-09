import os
import json
import ssl
import time
import hmac
import hashlib
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime
from zoneinfo import ZoneInfo

# === CONFIG ===
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"
PORT = 8883 if ENABLE_TLS else 1883
HMAC_SECRET = os.getenv("HMAC_SECRET")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "postgres_db"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname": os.getenv("DB_NAME", "iot_logs")
}

FILTERED_TOPICS = {
    "building/filtered/zone2/temperature": "building/zone2/ac/control",
    "building/filtered/zone1/motion": "building/zone1/door/lock",
    "building/filtered/zone3/gas": "building/zone3/alarm/control"
}
ACTUATOR_FEEDBACK = {
    "building/zone1/door/state": "Door Lock",
    "building/zone2/ac/state": "HVAC",
    "building/zone3/alarm/state": "Gas Alarm"
}

TEMP_THRESHOLD = 0.5
GAS_THRESHOLD = 10
HEARTBEAT_TOPIC = "hub/heartbeat"
HEARTBEAT_INTERVAL = 5
sensor_states = {}

# === HMAC UTILS ===
def compute_hmac(pkt):
    data = {k: pkt[k] for k in sorted(pkt) if k != "hmac"}
    return hmac.new(HMAC_SECRET.encode(), json.dumps(data, separators=(",", ":"), sort_keys=True).encode(), hashlib.sha256).hexdigest()

def verify_hmac(pkt):
    if not ENABLE_HMAC:
        return True
    return pkt.get("hmac") and hmac.compare_digest(compute_hmac(pkt), pkt["hmac"])

# === UTILS ===
def get_timestamp():
    return datetime.now(ZoneInfo("Europe/Rome")).strftime("%d/%b/%y %H:%M:%S")

def log_to_db(table, device_id, payload):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        timestamp = datetime.now(ZoneInfo("Europe/Rome"))
        cursor.execute(
            f"INSERT INTO {table} (device_id, payload, timestamp) VALUES (%s, %s, %s)",
            (device_id, json.dumps(payload), timestamp)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Hub]  DB log failed: {e}")

# === MQTT ===
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

def on_connect(client, userdata, flags, rc):
    print("[Hub]  Connected.")
    for t in FILTERED_TOPICS:
        client.subscribe(t)
    for t in ACTUATOR_FEEDBACK:
        client.subscribe(t)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if not verify_hmac(payload):
            print("[Hub]  Invalid HMAC — rejected.")
            return

        device_id = payload.get("device_id", "unknown")
        topic = msg.topic
        payload.pop("hmac", None)

        # === MOTION
        if topic == "building/filtered/zone1/motion":
            state = payload.get("value")
            if sensor_states.get(topic) != state:
                sensor_states[topic] = state
                action = "unlock" if state == "motion_detected" else "lock"
                cmd = {"action": action, "device_id": "hub", "timestamp": get_timestamp()}
                cmd["hmac"] = compute_hmac(cmd)
                client.publish("building/zone1/door/lock", json.dumps(cmd))
                print(f"[Hub]  Door command: {action.upper()}")

        # === GAS
        elif topic == "building/filtered/zone3/gas":
            level = payload.get("value")
            prev = sensor_states.get(topic)
            if prev is None or abs(prev - level) >= GAS_THRESHOLD:
                sensor_states[topic] = level
                state = "danger" if level >= 1000 else "warning" if level >= 300 else "normal"
                cmd = {"state": state, "value": level, "device_id": "hub", "timestamp": get_timestamp()}
                cmd["hmac"] = compute_hmac(cmd)
                client.publish("building/zone3/alarm/control", json.dumps(cmd))
                print(f"[Hub]  Gas state: {state.upper()}")

        # === TEMPERATURE
        elif topic == "building/filtered/zone2/temperature":
            temp = payload.get("value")
            prev = sensor_states.get(topic)
            if prev is None or abs(prev - temp) >= TEMP_THRESHOLD:
                sensor_states[topic] = temp
                cmd = {"sensor": "temperature", "value": temp, "device_id": "hub", "timestamp": get_timestamp()}
                cmd["hmac"] = compute_hmac(cmd)
                client.publish("building/zone2/ac/control", json.dumps(cmd))
                print(f"[Hub]  Temp control: {temp}°C")

        # === FEEDBACK or SENSOR LOGGING
        if topic in ACTUATOR_FEEDBACK:
            print(f"[Hub]  {ACTUATOR_FEEDBACK[topic]} reports: {payload.get('state')}")
            log_to_db("actuator_actions", device_id, payload)
        else:
            log_to_db("sensor_data", device_id, payload)

    except Exception as e:
        print(f"[Hub]  {e}")

client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, port=PORT)
client.loop_start()

# === HEARTBEAT LOOP ===
while True:
    hb = {"hub_status": "alive", "timestamp": get_timestamp(), "device_id": "hub"}
    hb["hmac"] = compute_hmac(hb)
    client.publish(HEARTBEAT_TOPIC, json.dumps(hb))
    time.sleep(HEARTBEAT_INTERVAL)

