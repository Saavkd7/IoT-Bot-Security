import os
import json
import time
import random
import paho.mqtt.client as mqtt
from datetime import datetime

# Environment & MQTT settings
BROKER = os.getenv("BROKER_ADDRESS", "mqtt_broker")
DEVICE_ID = "ac_unit_01"
CONTROL_TOPIC = "building/zone2/ac/control"   # Received from hub (payload includes measured and target temps)
STATE_TOPIC = "building/zone2/ac/state"         # Publish HVAC state

# Simulation parameters
current_temp = 22.0     # initial simulated room temperature
Kp = 0.2                # proportional control constant (tune this for responsiveness)
MIN_ADJUSTMENT = 0.1    # minimal temperature change to trigger an action
MAX_STEP = 1.0          # maximum change per update, to avoid sudden jumps

def on_message(client, userdata, msg):
    global current_temp
    try:
        payload = json.loads(msg.payload.decode())
        # Expected payload keys: "value" (measured temperature) and optionally "target"
        measured_temp = payload.get("value", current_temp)
        target_temp = payload.get("target", 22.0)
        timestamp = payload.get("timestamp", time.time())

        # Compute error as difference between current room state and target
        error = current_temp - target_temp

        # If the error is negligible, do nothing.
        if abs(error) < MIN_ADJUSTMENT:
            adjustment = 0.0
            action = "stable"
        else:
            # Proportional control: adjust a fraction of the error (negative error implies need for heating)
            adjustment = -Kp * error
            # Clamp the adjustment to avoid large jumps
            adjustment = max(min(adjustment, MAX_STEP), -MAX_STEP)
            action = "cooling" if adjustment < 0 else "heating"

        # Update the current temperature with the computed adjustment and add a small noise factor
        current_temp += adjustment + random.uniform(-0.05, 0.05)
        current_temp = round(current_temp, 2)

        # Create the state payload to publish
        state_payload = {
            "device_id": DEVICE_ID,
            "action": f"{action}: {abs(round(adjustment, 2))}°C",
            "current_temp": current_temp,
            "target_temp": target_temp,
            "timestamp": time.time()
        }
        client.publish(STATE_TOPIC, json.dumps(state_payload))
        print(f"[HVAC] {action} applied. New Temp: {current_temp}°C (Target: {target_temp}°C, Error: {error:.2f}°C)")
    except Exception as e:
        print(f"[HVAC] Error: {e}")

def main():
    client = mqtt.Client()
    client.connect(BROKER)
    client.subscribe(CONTROL_TOPIC)
    client.on_message = on_message
    print("[HVAC] Smart HVAC system is ONLINE. Listening for control commands...")
    client.loop_forever()

if __name__ == "__main__":
    main()

