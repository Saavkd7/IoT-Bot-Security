import os, json, time, ssl, random, hmac, hashlib
import paho.mqtt.client as mqtt
from datetime import datetime

# === CONFIG ===
BROKER        = os.getenv("BROKER_ADDRESS", "mqtt-broker")
PORT          = 8883 if os.getenv("ENABLE_TLS", "false").lower() == "true" else 1883
USERNAME      = os.getenv("MQTT_USERNAME", "")
PASSWORD      = os.getenv("MQTT_PASSWORD", "")
ENABLE_TLS    = os.getenv("ENABLE_TLS", "false").lower() == "true"
ENABLE_AUTH   = os.getenv("ENABLE_AUTH", "false").lower() == "true"
ENABLE_HMAC   = os.getenv("ENABLE_HMAC", "true").lower() == "true"
HMAC_SECRET   = os.getenv("HMAC_SECRET", "defaultsecret").encode()

TOPIC         = "building/zone2/temperature/room1"
HEARTBEAT     = "hub/heartbeat"
DEVICE_ID     = "sensor_temp_01"
last_hb       = time.time()

# === UTILS ===
def now_str():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def sign(pkt):
    if not ENABLE_HMAC:
        return ""
    raw = json.dumps({k: pkt[k] for k in sorted(pkt)}, separators=(",", ":"), sort_keys=True).encode()
    return hmac.new(HMAC_SECRET, raw, hashlib.sha256).hexdigest()

# === MQTT CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    print("[TEMP SENSOR] Connected.")
    client.subscribe(HEARTBEAT)

def on_message(client, userdata, msg):
    global last_hb
    if msg.topic == HEARTBEAT:
        last_hb = time.time()

# === MQTT CLIENT SETUP ===
client = mqtt.Client()
if ENABLE_AUTH:
    client.username_pw_set(USERNAME, PASSWORD)
if ENABLE_TLS:
    client.tls_set(ca_certs="/mosquitto/certs/ca.crt", cert_reqs=ssl.CERT_REQUIRED)

client.on_connect  = on_connect
client.on_message  = on_message
client.reconnect_delay_set(1, 30)

# === CONNECT LOOP ===
while True:
    try:
        client.connect(BROKER, port=PORT)
        break
    except Exception as e:
        print(f"[TEMP SENSOR] Retrying: {e}")
        time.sleep(3)

client.loop_start()
print("[TEMP SENSOR] Waiting for heartbeat...")


while True:
    if time.time() - last_hb <= 10:
        temp = round(random.uniform(19.0, 25.0), 2)
        pkt = {
            "device_id": DEVICE_ID,
            "sensor": "temperature",
            "value": temp,
            "timestamp": now_str()
        }
        if ENABLE_HMAC:
            pkt["hmac"] = sign(pkt)
        client.publish(TOPIC, json.dumps(pkt))
        print(f"[TEMP SENSOR] Temp: {temp} °C")
    else:
        print("[TEMP SENSOR] Paused (hub offline)")
    time.sleep(5)

