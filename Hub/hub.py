import os
import json
import time
import paho.mqtt.client as mqtt
import psycopg2

# MQTT Broker Address
BROKER_ADDRESS = os.getenv("BROKER_ADDRESS", "mqtt_broker")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "postgres_db")
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "iot_logs"

# Sensor-to-Actuator Mapping
SENSOR_TOPICS = {
    "building/zone2/temperature/room1": "building/zone2/ac/control",
    "building/zone1/motion/entrance": "building/zone1/door/lock",
    "building/zone3/gas/detection": "building/zone3/alarm/control"
}

# Mapping for Actuator State Messages
ACTUATOR_STATE_TOPICS = {
    "building/zone2/ac/state": "HVAC",
    "building/zone1/door/state": "Door Lock",
    "building/zone3/alarm/state": "Gas Alarm"
}

# Sensor State Storage
sensor_states = {}

# Threshold Values for Significant Changes
TEMP_THRESHOLD = 0.5  # Temperature difference must be >= 0.5°C
GAS_THRESHOLD = 10    # Gas level difference must be >= 10 PPM

# Database Logging Function
def log_to_database(device_id, event, payload):
    """Log sensor and actuator events to the database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO network_logs (device_id, event, payload, timestamp) VALUES (%s, %s, %s, %s)",
            (device_id, event, json.dumps(payload), time.time()),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"[Central Hub] ⚠️ Database is unreachable. Skipping logging. Error: {e}")
    except Exception as e:
        print(f"[Central Hub] ❌ Database logging error: {e}")

# MQTT Message Processing
def on_message(client, userdata, msg):
    """Process sensor data and trigger actuator commands based on incoming messages."""
    print(f"📥 Received message: {msg.payload.decode()} on topic: {msg.topic}")

    try:
        data = json.loads(msg.payload.decode())
        sensor_id = data.get("sensor", "unknown")

        # Process Motion Sensor Messages
        if msg.topic == "building/zone1/motion/entrance":
            if "value" in data:
                motion_state = data["value"]
                if msg.topic not in sensor_states or sensor_states[msg.topic] != motion_state:
                    sensor_states[msg.topic] = motion_state
                    # Determine door action based on motion state
                    action = "unlock" if motion_state == "motion_detected" else "lock"
                    client.publish("building/zone1/door/lock", json.dumps({"action": action}))
                    print(f"📢 Motion: {motion_state} | Command sent: {action}")
            else:
                print("⚠️ Warning: 'value' key missing in motion message")

        # Process Gas Sensor Messages
        elif msg.topic == "building/zone3/gas/detection":
            if "value" in data:
                gas_level = data["value"]
                # Only forward if significant change occurs
                if msg.topic not in sensor_states or abs(sensor_states[msg.topic] - gas_level) >= GAS_THRESHOLD:
                    sensor_states[msg.topic] = gas_level
                    action = "activate" if gas_level > 300 else "deactivate"
                    client.publish("building/zone3/alarm/control", json.dumps({"action": action}))
                    print(f"📢 Gas Level: {gas_level} PPM | Command sent: {action}")
            else:
                print("⚠️ Warning: 'value' key missing in gas detection message")

        # Process Temperature Sensor Messages
        elif msg.topic == "building/zone2/temperature/room1":
            if "value" in data:
                temp = data["value"]
                # Check if change is significant before forwarding
                if msg.topic not in sensor_states or abs(sensor_states[msg.topic] - temp) >= TEMP_THRESHOLD:
                    sensor_states[msg.topic] = temp
                    # Forward the raw temperature reading to HVAC actuator
                    payload = {
                        "sensor": "temperature",
                        "value": temp,
                        "timestamp": time.time()
                    }
                    client.publish("building/zone2/ac/control", json.dumps(payload))
                    print(f"📢 Temperature reading: {temp}°C → forwarded to HVAC for adjustment.")
            else:
                print("⚠️ Warning: 'value' key missing in temperature message")

        # Process Actuator State Messages
        elif msg.topic in ACTUATOR_STATE_TOPICS:
            actuator_name = ACTUATOR_STATE_TOPICS[msg.topic]
            if "state" in data:
                print(f"✅ {actuator_name} confirmed state: {data['state']}")
            else:
                print(f"⚠️ Warning: 'state' key missing in actuator state message")

        # Log event to database if sensor info is present
        if "sensor" in data:
            log_to_database(sensor_id, "sensor_data", data)

    except json.JSONDecodeError:
        print("❌ Invalid JSON format received.")

# MQTT Client Setup
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # Using newer Callback API
    client.on_message = on_message
    client.connect(BROKER_ADDRESS)

    # Subscribe to sensor topics and actuator state topics
    for topic in SENSOR_TOPICS.keys():
        client.subscribe(topic)
    for topic in ACTUATOR_STATE_TOPICS.keys():
        client.subscribe(topic)

    print("[Central Hub] 🌐 I am ONLINE! Monitoring sensors and actuators...")
    client.loop_forever()

if __name__ == "__main__":
    main()

