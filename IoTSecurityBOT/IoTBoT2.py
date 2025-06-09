#!/usr/bin/env python3
# IoTBoT.py  ── DB‑driven allow‑list + full anomaly logging
import os, json, ssl, hmac, hashlib, time, psycopg2
import paho.mqtt.client as mqtt
from collections import defaultdict
from datetime import datetime, timezone

# ─── CONFIG ─────────────────────────────────────────────────────────────
BROKER        = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT          = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME      = os.getenv("MQTT_USERNAME", "")
PASSWORD      = os.getenv("MQTT_PASSWORD", "")
TLS           = os.getenv("ENABLE_TLS",  "false").lower() == "true"
AUTH          = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC   = os.getenv("ENABLE_HMAC", "true").lower() == "true"
HMAC_SECRET   = os.getenv("HMAC_SECRET", "123iot45").encode()

DB_PARAMS = {
    "host":     os.getenv("DB_HOST", "postgres_db"),
    "port":     os.getenv("DB_PORT", "5432"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname":   os.getenv("DB_NAME", "iot_logs")
}

RAW_TOPICS = [
    "building/zone2/temperature/room1",
    "building/zone1/motion/entrance",
    "building/zone3/gas/detection",
    "device/registration"
]
FORWARD_MAP = {
    "building/zone2/temperature/room1": "building/filtered/zone2/temperature",
    "building/zone1/motion/entrance":  "building/filtered/zone1/motion",
    "building/zone3/gas/detection":    "building/filtered/zone3/gas"
}

RATE_LIMIT   = defaultdict(list)
QUARANTINE   = set()
ALLOWED_KEYS = {"device_id","sensor","value","state","timestamp","hmac","action"}

# ─── DB HELPERS ─────────────────────────────────────────────────────────
def log_anomaly(device_id, payload):
    try:
        with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO anomaly_logs (device_id,payload,timestamp) VALUES (%s,%s,%s)",
                (device_id, json.dumps(payload), datetime.now(timezone.utc))
            )
        print(f"[IoTBot] 📝 Logged anomaly for {device_id}")
    except Exception as e:
        print(f"[IoTBot] ⚠️ Failed to log anomaly: {e}")

def load_registered_devices():
    try:
        with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS registered_devices "
                "(device_id TEXT PRIMARY KEY, registered_at TIMESTAMPTZ)"
            )
            cur.execute("SELECT device_id FROM registered_devices")
            ids = {row[0] for row in cur.fetchall()}
        print(f"[IoTBot] 🔄 Loaded {len(ids)} registered devices from DB")
        return ids
    except Exception as e:
        print(f"[IoTBot] ⚠️ Cannot load registered devices: {e}")
        return set()

def register_device(device_id):
    """Optional dynamic registration (comment call-site if you want static list only)."""
    try:
        with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO registered_devices (device_id,registered_at) "
                "VALUES (%s,now()) ON CONFLICT DO NOTHING",
                (device_id,)
            )
        print(f"[IoTBot] ✅ Registered device: {device_id}")
        REGISTERED.add(device_id)
    except Exception as e:
        print(f"[IoTBot] ⚠️ Failed to register device: {e}")

REGISTERED = load_registered_devices()

# ─── SECURITY UTILITIES ────────────────────────────────────────────────
def compute_hmac(pkt):
    data = {k:pkt[k] for k in sorted(pkt) if k!="hmac"}
    raw  = json.dumps(data, separators=(",",":"), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, raw, hashlib.sha256).hexdigest()

def verify_hmac(pkt):
    if not ENABLE_HMAC:                 # HMAC disabled globally
        return True
    sig = pkt.get("hmac")
    return sig and hmac.compare_digest(compute_hmac(pkt), sig)

def is_sqli_like(dev_id):
    bad = ["'", '"', ";", "--", "drop", "insert", "update", "delete"]
    return any(x in dev_id.lower() for x in bad)

def is_malware(pkt):
    return any(k not in ALLOWED_KEYS for k in pkt)

# ─── MQTT SETUP ────────────────────────────────────────────────────────
client = mqtt.Client()
if AUTH: client.username_pw_set(USERNAME, PASSWORD)
if TLS:  client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

def on_connect(cl, userdata, flags, rc):
    print("[IoTBot] ✅ Connected to broker.")
    for t in RAW_TOPICS: cl.subscribe(t)

def on_disconnect(cl, userdata, rc):
    print("[IoTBot] 🔌 Disconnected from broker.")

def on_message(cl, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        device_id = data.get("device_id") or data.get("sensor") or "unknown"

        print(f"[IoTBot] 📩 {msg.topic} ← {device_id}")

        # --- Quarantine check ---
        if device_id in QUARANTINE:
            log_anomaly(device_id, {"event":"quarantined", "payload":data})
            return

        # --- Allow‑list check ---
        if device_id not in REGISTERED:
            log_anomaly(device_id, {"event":"unregistered_device", "payload":data})
            QUARANTINE.add(device_id)
            print(f"[IoTBot] 🚫 {device_id} is not registered — quarantined.")
            return

        # --- Security checks ---
        if not verify_hmac(data):
            log_anomaly(device_id, {"event":"invalid_hmac","payload":data})
            QUARANTINE.add(device_id); return

        if is_sqli_like(device_id):
            log_anomaly(device_id, {"event":"sql_injection","payload":data})
            QUARANTINE.add(device_id); return

        if is_malware(data):
            log_anomaly(device_id, {"event":"malware_injection","payload":data})
            QUARANTINE.add(device_id); return

        # --- DDoS rate limiting ---
        now = time.time()
        RATE_LIMIT[device_id] = [t for t in RATE_LIMIT[device_id] if t > now-10]
        RATE_LIMIT[device_id].append(now)
        if len(RATE_LIMIT[device_id]) > 5:
            log_anomaly(device_id, {"event":"ddos_detected","payload":data})
            return

        # --- OPTIONAL auto‑add new device on first clean contact ---
        # if device_id not in REGISTERED:
        #     register_device(device_id)

        # --- Forward to filtered topic ---
        forward_topic = FORWARD_MAP.get(msg.topic)
        if forward_topic:
            cl.publish(forward_topic, msg.payload)
            print(f"[IoTBot] ✅ Forwarded clean message to {forward_topic}")

    except Exception as e:
        print(f"[IoTBot] ❌ Processing error: {e}")

client.on_connect    = on_connect
client.on_disconnect = on_disconnect
client.on_message    = on_message
client.reconnect_delay_set(1, 30)

client.connect(BROKER, PORT)
client.loop_start()
print("[IoTBot] 🧱 Real‑time defence running...")
while True:
    time.sleep(5)

