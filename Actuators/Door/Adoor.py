import os, json, time
import paho.mqtt.client as mqtt

BROKER = os.getenv("BROKER_ADDRESS", "mqtt_broker")
DEVICE_ID = "door_lock_01"
CONTROL_TOPIC = "building/zone1/door/lock"
STATE_TOPIC = "building/zone1/door/state"

current_state = "locked"

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
                "timestamp": time.time()
            }))
    except Exception as e:
        print(f"[Door] ❌ Error processing message: {e}")

def main():
    client = mqtt.Client()
    client.connect(BROKER)
    client.subscribe(CONTROL_TOPIC)
    client.on_message = on_message
    print(f"[Door] 🔐 ONLINE at {CONTROL_TOPIC}")
    client.publish(STATE_TOPIC, json.dumps({
        "state": current_state,
        "device_id": DEVICE_ID,
        "timestamp": time.time()
    }))
    client.loop_forever()

if __name__ == "__main__":
    main()

