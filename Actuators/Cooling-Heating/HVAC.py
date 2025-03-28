import os
import json
import random
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = os.getenv("BROKER_ADDRESS", "mqtt_broker")
DEVICE_ID = "ac_unit_01"
CONTROL_TOPIC = "building/zone2/ac/control"   # Commands with measured and target temperatures
STATE_TOPIC = "building/zone2/ac/state"         # Publish HVAC state updates

current_temp = 22.0     # Initial simulated room temperature
Kp = 0.2                # Proportional control constant
MIN_ADJUSTMENT = 0.1    # Minimal temperature change to trigger an action
MAX_STEP = 1.0          # Maximum change per update

def get_formatted_timestamp():
    return datetime.now().strftime("%d/%m/%y")

def on_message(client, userdata, msg):
    global current_temp
    try:
        payload = json.loads(msg.payload.decode())
        # Expected keys: "value" (measured temperature) and optionally "target"
        measured_temp = payload.get("value", current_temp)
        target_temp = payload.get("target", 22.0)
        
        error = current_temp - target_temp
        
        if abs(error) < MIN_ADJUSTMENT:
            adjustment = 0.0
            action = "stable"
        else:
            adjustment = -Kp * error
            adjustment = max(min(adjustment, MAX_STEP), -MAX_STEP)
            action = "cooling" if adjustment < 0 else "heating"
        
        # Update the simulated temperature with slight random noise
        current_temp += adjustment + random.uniform(-0.05, 0.05)
        current_temp = round(current_temp, 2)
        
        state_payload = {
            "device_id": DEVICE_ID,
            "action": f"{action}: {abs(round(adjustment, 2))}°C",
            "current_temp": current_temp,
            "target_temp": target_temp,
            "timestamp": get_formatted_timestamp()
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

