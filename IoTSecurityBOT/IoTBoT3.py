import os
import json
import ssl
import hmac
import hashlib
import time
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime, timezone
from collections import defaultdict

# ─── CONFIG ─────────────────────────────────────────────────────────────
BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
HMAC_SECRET = os.getenv("HMAC_SECRET", "123iot45").encode()
TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC = os.getenv("ENABLE_HMAC", "true").lower() == "true"

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "postgres_db"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname": os.getenv("DB_NAME", "iot_logs")
}

RAW_TOPICS = [
    "building/zone2/temperature/room1",
    "building/zone1/motion/entrance",
    "building/zone3/gas/detection",
    "device/registration"
]
FORWARD_MAP = {
    "building/zone2/temperature/room1": "building/filtered/zone2/temperature",
    "building/zone1/motion/entrance": "building/filtered/zone1/motion",
    "building/zone3/gas/detection": "building/filtered/zone3/gas"
}
KNOWN_DEVICES = {"sensor_motion_01", "sensor_temp_01", "sensor_gas_01", "door_lock_01", "hvac_01", "alarm_gas_01", "hub"}
RATE_LIMIT = defaultdict(list)
QUARANTINE = set()
ALLOWED_KEYS = {"device_id", "sensor", "value", "state", "timestamp", "hmac", "hub_status", "action"}

# ─── DDoS GUARD ─────────────────────────────────────────────────────────
NEW_DEVICE_WINDOW = 30
NEW_DEVICE_LIMIT = 10
NEW_DEVICES_LOG = []

DDOS_GLOBAL_WINDOW = 10
DDOS_GLOBAL_MAX = 100
GLOBAL_FLOOD_LOG = []

GLOBAL_DDOS_MODE = False  

def is_global_ddos():
    now = time.time()
    GLOBAL_FLOOD_LOG[:] = [t for t in GLOBAL_FLOOD_LOG if now - t < DDOS_GLOBAL_WINDOW]
    GLOBAL_FLOOD_LOG.append(now)
    return len(GLOBAL_FLOOD_LOG) > DDOS_GLOBAL_MAX

def is_ddos_from_new_ids(device_id):
    now = time.time()
    NEW_DEVICES_LOG[:] = [t for t in NEW_DEVICES_LOG if now - t[0] < NEW_DEVICE_WINDOW]
    if device_id not in KNOWN_DEVICES and device_id not in QUARANTINE:
        NEW_DEVICES_LOG.append((now, device_id))
    ids = {d for _, d in NEW_DEVICES_LOG}
    return len(ids) > NEW_DEVICE_LIMIT

# ─── SECURITY UTILS ─────────────────────────────────────────────────────
def compute_hmac(payload_dict):
    data = {k: payload_dict[k] for k in sorted(payload_dict) if k != "hmac"}
    raw = json.dumps(data, separators=(",", ":"), sort_keys=True)
    return hmac.new(HMAC_SECRET, raw.encode(), hashlib.sha256).hexdigest()

def verify_hmac(payload_dict):
    if not ENABLE_HMAC:
        return True
    received = payload_dict.get("hmac")
    return received and hmac.compare_digest(compute_hmac(payload_dict), received)

def is_sqli_like(device_id):
    suspicious = ["'", '"', ";", "--", "drop", "insert", "update", "delete"]
    return any(x in device_id.lower() for x in suspicious)

def is_malware(payload_dict):
    return any(k not in ALLOWED_KEYS for k in payload_dict)

def log_anomaly(device_id, payload):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO anomaly_logs (device_id, payload, timestamp) VALUES (%s, %s, %s)",
            (device_id, json.dumps(payload), datetime.now(timezone.utc))
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[IoTBot]  Logged anomaly for {device_id}")
    except Exception as e:
        print(f"[IoTBot]  Failed to log anomaly: {e}")
        
        
REGISTERED = set()

def register_device(device_id):
    if device_id in REGISTERED:
        return
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO registered_devices (device_id, registered_at) VALUES (%s, now()) ON CONFLICT DO NOTHING",
            (device_id,)
        )
        if cur.rowcount > 0:
            print(f"[IoTBot]  Registered device: {device_id}")
        REGISTERED.add(device_id)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[IoTBot]  Failed to register device: {e}")
        
# ─── MQTT CLIENT SETUP ──────────────────────────────────────────────────
client = mqtt.Client()
if AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

def on_connect(client, userdata, flags, rc):
    print("[IoTBot]  Connected to broker.")
    client.subscribe("#")  # ALL topics

def on_disconnect(client, userdata, rc):
    print("[IoTBot]  Disconnected from broker.")

def on_message(client, userdata, msg):
    global GLOBAL_DDOS_MODE
    try:
        data = json.loads(msg.payload.decode())
        device_id = data.get("device_id") or data.get("sensor")

        # === GLOBAL DDoS CHECK ===
        if is_global_ddos():
            GLOBAL_DDOS_MODE = True
            print("[IoTBot]  GLOBAL DDoS MODE TRIGGERED")

        # === Smart Mitigation ===
        if GLOBAL_DDOS_MODE and device_id not in KNOWN_DEVICES:
            print(f"[IoTBot]  {device_id} dropped (DDoS mode)")
            log_anomaly(device_id, {"event": "ddos_mode_drop", "payload": data})
            return

        if is_ddos_from_new_ids(device_id):
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "new_device_ddos", "payload": data})
            return

        if device_id in QUARANTINE:
            log_anomaly(device_id, {"event": "quarantined", "payload": data})
            return

        if msg.topic == "device/registration" and device_id not in KNOWN_DEVICES:
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "unauthorized_registration", "payload": data})
            return

        if not verify_hmac(data):
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "invalid_hmac", "payload": data})
            return

        if is_sqli_like(device_id):
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "sql_injection", "payload": data})
            return

        if is_malware(data):
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "malware", "payload": data})
            return

        RATE_LIMIT[device_id] = [t for t in RATE_LIMIT[device_id] if t > time.time() - 10]
        RATE_LIMIT[device_id].append(time.time())
        if len(RATE_LIMIT[device_id]) > 50:
            QUARANTINE.add(device_id)
            log_anomaly(device_id, {"event": "ddos_rate_limit", "payload": data})
            return

        if device_id in KNOWN_DEVICES:
            register_device(device_id)

        forward_topic = FORWARD_MAP.get(msg.topic)
        if forward_topic:
            client.publish(forward_topic, msg.payload)
            print(f"[IoTBot]  Forwarded from {device_id} → {forward_topic}")
    except Exception as e:
        print(f"[IoTBot] Error: {e}")

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(1, 30)
client.connect(BROKER, port=PORT)
client.loop_start()
print("[IoTBot]  Defense system running...")

while True:
    time.sleep(5)

