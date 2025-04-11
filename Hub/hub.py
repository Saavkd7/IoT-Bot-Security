import os
import json
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone handling


BROKER = os.getenv("BROKER_ADDRESS", "mqtt-broker")
USERNAME = os.getenv("MQTT_USERNAME", "iotuser")
PASSWORD = os.getenv("MQTT_PASSWORD", "iotpassword")



DB_HOST = os.getenv("DB_HOST", "postgres_db")
DB_PORT = "5432"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "iot_logs")

SENSOR_TOPICS = {
    "building/zone2/temperature/room1": "building/zone2/ac/control",
    "building/zone1/motion/entrance": "building/zone1/door/lock",
    "building/zone3/gas/detection": "building/zone3/alarm/control"
}

ACTUATOR_STATE_TOPICS = {
    "building/zone2/ac/state": "HVAC",
    "building/zone1/door/state": "Door Lock",
    "building/zone3/alarm/state": "Gas Alarm"
}

sensor_states = {}
TEMP_THRESHOLD = 0.5
GAS_THRESHOLD = 10

def fix_schema():
    """
    Force the 'timestamp' column to become TIMESTAMPTZ by dropping the old column
    and re-adding it. This removes old data in that column but prevents type conflicts.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, dbname=DB_NAME
        )
        cursor = conn.cursor()
        
        # 1. Drop the old 'timestamp' column if it exists
        drop_sql = "ALTER TABLE network_logs DROP COLUMN IF EXISTS timestamp;"
        cursor.execute(drop_sql)

        # 2. Add a new 'timestamp' column of type TIMESTAMPTZ
        add_sql = "ALTER TABLE network_logs ADD COLUMN timestamp TIMESTAMPTZ;"
        cursor.execute(add_sql)

        conn.commit()
        cursor.close()
        conn.close()
        print("[Hub] ✅ Successfully dropped and re-added 'timestamp' as TIMESTAMPTZ.")
    except psycopg2.Error as e:
        print(f"[Hub] ❌ Could not fix 'timestamp' column: {e}")
    except Exception as e:
        print(f"[Hub] ❌ Unexpected error fixing 'timestamp' column: {e}")

def get_local_timestamp():
    """
    Return a timezone-aware datetime for Europe/Rome.
    Ensures timestamps reflect local Italy time (including DST).
    """
    return datetime.now(ZoneInfo("Europe/Rome"))

def get_formatted_timestamp():
    """
    Return a human-readable local datetime string.
    Example: "29/Mar/25 13:33:07"
    """
    return get_local_timestamp().strftime("%d/%b/%y %H:%M:%S")

def log_to_database(device_id, event, payload):
    """
    Insert a row into the network_logs table.
    The 'timestamp' column is stored as a true TIMESTAMPTZ.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER,
            password=DB_PASSWORD, dbname=DB_NAME
        )
        cursor = conn.cursor()

        # Keep a human-readable string in the payload for reference
        payload["hub_timestamp"] = get_formatted_timestamp()
        # Insert a proper timezone-aware datetime
        db_timestamp = get_local_timestamp()

        cursor.execute(
            """
            INSERT INTO network_logs (device_id, event, payload, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (device_id, event, json.dumps(payload), db_timestamp)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"[Hub] ⚠️ Database is unreachable. Skipping logging. Error: {e}")
    except Exception as e:
        print(f"[Hub] ❌ Database logging error: {e}")

def on_message(client, userdata, msg):
    print(f"📥 Received message: {msg.payload.decode()} on topic: {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        sensor_id = data.get("sensor", "unknown")

        # Process Motion Sensor
        if msg.topic == "building/zone1/motion/entrance":
            if "value" in data:
                motion_state = data["value"]
                if msg.topic not in sensor_states or sensor_states[msg.topic] != motion_state:
                    sensor_states[msg.topic] = motion_state
                    action = "unlock" if motion_state == "motion_detected" else "lock"
                    client.publish("building/zone1/door/lock", json.dumps({
                        "action": action,
                        "timestamp": get_formatted_timestamp()
                    }))
                    print(f"📢 Motion: {motion_state} | Command sent: {action}")
            else:
                print("⚠️ Warning: 'value' key missing in motion message")

        # Process Gas Sensor
        elif msg.topic == "building/zone3/gas/detection":
            if "value" in data:
                gas_level = data["value"]
                if msg.topic not in sensor_states or abs(sensor_states[msg.topic] - gas_level) >= GAS_THRESHOLD:
                    sensor_states[msg.topic] = gas_level
                    action = "activate" if gas_level > 300 else "deactivate"
                    client.publish("building/zone3/alarm/control", json.dumps({
                        "action": action,
                        "timestamp": get_formatted_timestamp()
                    }))
                    print(f"📢 Gas Level: {gas_level} PPM | Command sent: {action}")
            else:
                print("⚠️ Warning: 'value' key missing in gas detection message")

        # Process Temperature Sensor
        elif msg.topic == "building/zone2/temperature/room1":
            if "value" in data:
                temp = data["value"]
                if msg.topic not in sensor_states or abs(sensor_states[msg.topic] - temp) >= TEMP_THRESHOLD:
                    sensor_states[msg.topic] = temp
                    payload = {
                        "sensor": "temperature",
                        "value": temp,
                        "timestamp": get_formatted_timestamp()
                    }
                    client.publish("building/zone2/ac/control", json.dumps(payload))
                    print(f"📢 Temperature reading: {temp}°C → forwarded to HVAC for adjustment.")
            else:
                print("⚠️ Warning: 'value' key missing in temperature message")

        # Process Actuator State
        elif msg.topic in ACTUATOR_STATE_TOPICS:
            actuator_name = ACTUATOR_STATE_TOPICS[msg.topic]
            if "state" in data:
                print(f"✅ {actuator_name} confirmed state: {data['state']}")
                log_to_database(actuator_name, "actuator_data", data)
            else:
                print(f"⚠️ Warning: 'state' key missing in actuator state message")

        # Log sensor event
        if "sensor" in data:
            log_to_database(sensor_id, "sensor_data", data)

    except json.JSONDecodeError:
        print("❌ Invalid JSON format received.")

def main():
    # Force the DB schema to drop the old 'timestamp' column and re-add it as TIMESTAMPTZ
    fix_schema()

    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_message = on_message
    client.connect(BROKER)

    for topic in SENSOR_TOPICS.keys():
        client.subscribe(topic)
    for topic in ACTUATOR_STATE_TOPICS.keys():
        client.subscribe(topic)

    print("[Hub] 🌐 I am ONLINE! Monitoring sensors and actuators...")
    client.loop_forever()

if __name__ == "__main__":
    main()

