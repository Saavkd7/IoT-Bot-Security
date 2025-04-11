import os
import json
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "iotuser")
PASSWORD = os.getenv("MQTT_PASSWORD", "iotpassword")


DEVICE_ID = "door_lock_01"
CONTROL_TOPIC = "building/zone1/door/lock"
STATE_TOPIC = "building/zone1/door/state"

current_state = "locked"

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def on_message(client, userdata, msg):
    global current_state
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("action")
        if command not in ["lock", "unlock"]:
            print(f"[Door] ⚠️ Invalid command: {command}")
            return
        if command != current_state:
            current_state = command
            print(f"[Door] 🚪 State changed to: {current_state}")
            client.publish(STATE_TOPIC, json.dumps({
                "state": current_state,
                "device_id": DEVICE_ID,
                "timestamp": get_formatted_timestamp()
            }))
    except Exception as e:
        print(f"[Door] ❌ Error processing message: {e}")

def main():

    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER)
    client.subscribe(CONTROL_TOPIC)
    client.on_message = on_message
    print(f"[Door] 🔐 ONLINE at {CONTROL_TOPIC}")
    client.publish(STATE_TOPIC, json.dumps({
        "state": current_state,
        "device_id": DEVICE_ID,
        "timestamp": get_formatted_timestamp()
    }))
    client.loop_forever()

if __name__ == "__main__":
    main()

