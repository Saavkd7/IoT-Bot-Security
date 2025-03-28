import os
import json
import time
import paho.mqtt.client as mqtt
from faker import Faker
from datetime import datetime

faker = Faker()
BROKER_ADDRESS = os.getenv("BROKER_ADDRESS", "mqtt_broker")
CONTROL_TOPIC = "building/zone2/ac/control"
STATE_TOPIC = "building/zone2/ac/state"
SENSOR_TOPIC = "building/zone2/temperature/room1"

# Initial settings
current_temp = 22.0  # Default indoor temperature
target_temp = {"winter": 22.0, "spring": 21.0, "summer": 23.0, "autumn": 21.0}  # Target comfort temp

def get_season():
    """Determine the current season based on the month."""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def on_message(client, userdata, message):
    global current_temp
    season = get_season()
    payload = json.loads(message.payload.decode())

    if "value" in payload:
        received_temp = payload["value"]
        print(f"[HVAC] 🌡️ Received Temperature: {received_temp}°C in {season}")

        # Get the target temperature based on the current season
        ideal_temp = target_temp[season]

        # Adjust heating or cooling based on season and temperature deviation
        if received_temp > ideal_temp + 2:
            adjustment = round(faker.pyfloat(min_value=-1.5, max_value=-0.5), 2)  # Gradual cooling
            current_temp += adjustment
            action = f"cooling: {abs(adjustment)}°C"
        elif received_temp < ideal_temp - 2:
            adjustment = round(faker.pyfloat(min_value=0.5, max_value=1.5), 2)  # Gradual heating
            current_temp += adjustment
            action = f"heating: {adjustment}°C"
        else:
            action = "stable"

        client.publish(STATE_TOPIC, json.dumps({"action": action, "current_temp": current_temp, "season": season}))
        print(f"[HVAC] 🔄 Adjusting: {action} | Room Temp: {current_temp}°C | Target: {ideal_temp}°C ({season})")

def main():
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS)
    client.subscribe(SENSOR_TOPIC)
    client.on_message = on_message

    print(f"[HVAC] Listening for temperature readings on {SENSOR_TOPIC}...")
    client.loop_forever()

if __name__ == "__main__":
    main()
