import os
import json
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = os.getenv("BROKER_ADDRESS", "mqtt_broker")
DEVICE_ID = "gas_alarm_01"
CONTROL_TOPIC = "building/zone3/alarm/control"
STATE_TOPIC = "building/zone3/alarm/state"

current_state = "deactivated"

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%b/%y %H:%M:%S")

def on_message(client, userdata, msg):
    global current_state
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("action")
        if command not in ["activate", "deactivate"]:
            print(f"[Gas Alarm] ⚠️ Invalid command: {command}")
            return
        if command != current_state:
            current_state = command
            print(f"[Gas Alarm] 🚨 State changed to: {current_state}")
            client.publish(STATE_TOPIC, json.dumps({
                "state": current_state,
                "device_id": DEVICE_ID,
                "timestamp": get_formatted_timestamp()
            }))
    except Exception as e:
        print(f"[Gas Alarm] ❌ Error processing message: {e}")

def main():
    client = mqtt.Client()
    client.connect(BROKER)
    client.subscribe(CONTROL_TOPIC)
    client.on_message = on_message
    print(f"[Gas Alarm] 🛑 ONLINE at {CONTROL_TOPIC}")
    client.publish(STATE_TOPIC, json.dumps({
        "state": current_state,
        "device_id": DEVICE_ID,
        "timestamp": get_formatted_timestamp()
    }))
    client.loop_forever()

if __name__ == "__main__":
    main()

