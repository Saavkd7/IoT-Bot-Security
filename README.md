
# 🛡️ IoTBot Security System

An advanced **IoT Security Framework** for smart buildings, designed to monitor, detect, and mitigate real-time cyberattacks on MQTT-based networks using Python, Docker, and PostgreSQL.

## 🧠 Overview

This project simulates a secure IoT infrastructure with multiple sensors and actuators controlled by a central hub. It includes:

- MQTT with optional **TLS**, **username/password authentication**, and **ACLs**
- **HMAC integrity checks** between devices
- A central **Hub** that routes, filters, and logs sensor events
- An intelligent **IoTBot** that detects and reacts to:
  - 🧨 DDoS attacks (rate-based + new device flood)
  - 💉 SQL Injection payloads
  - 🦠 Malformed/malware-like payloads
  - 🔓 Unauthorized device registration
- Full device simulation: gas, motion, temperature sensors and actuators (HVAC, Door, Alarm)
- An MQTT **Sniffer** to simulate credential theft via MITM attacks

## 📂 Architecture

```
┌────────┐     MQTT (TLS)     ┌────────┐     MQTT (Filtered)     ┌──────────┐
│Sensor  │ ────────────────▶ │  Hub   │ ───────────────────────▶│ Actuator │
│(Temp)  │                   └────────┘                          │ (HVAC)   │
│(Motion)│                                                   ▲  └──────────┘
│(Gas)   │ ───── Heartbeats ──────▶                         Logs
└────────┘                     ▼                             ▼
                             [IoTBot] (Monitor & Defend) ─▶ PostgreSQL
```

## 🔐 Security Features

| Mechanism       | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| **HMAC**        | Ensures message integrity across all components using a shared secret key. |
| **TLS**         | Encrypts MQTT traffic using CA-signed certificates.                         |
| **Auth + ACL**  | Restricts MQTT access by user and topic.                                    |
| **SQLi Guard**  | Blocks malicious identifiers attempting SQL injection.                      |
| **Rate Limiting**| Blocks devices that exceed safe message thresholds.                        |
| **Device Quarantine**| Isolates unknown or compromised devices.                              |

## 🧪 Attack Simulations

✅ The following attacks are simulated and mitigated in real-time:

| Attack Type     | Method                          | Detection/Mitigation Script   |
|-----------------|----------------------------------|-------------------------------|
| DDoS            | Flooding from fake IDs           | `IoTBoT3.py` (rate limit, global) |
| MITM Sniffing   | Credential theft via `tcpdump`   | `Sniffer.py`                  |
| SQL Injection   | Malicious `device_id` injection  | `SQLinjection.py`            |
| Spoofing        | Forged data with invalid HMAC    | Rejected in Hub & IoTBot     |
| Hijacking       | Commands from unauthorized hub   | Rejected via HMAC validation |

## 🚀 Components

| Role       | Script           | Description                         |
|------------|------------------|-------------------------------------|
| 🧠 Hub     | `hub.py`         | Routes, filters, and commands actuators |
| 🤖 IoTBot  | `IoTBoT3.py`     | Monitors MQTT traffic & detects threats |
| 🌡️ Sensors | `stemp.py`, `sgas.py`, `smotion.py` | Simulate data, respond to heartbeat |
| 🔐 Actuators | `HVAC.py`, `Adoor.py`, `GasActuator.py` | React to hub commands & report state |
| 🕵️ Sniffer | `Sniffer.py`     | Captures MQTT credentials (non-TLS)  |
| 💉 SQLi     | `SQLinjection.py`| Injects fake device with SQL payload |

## 🛠️ Configuration Modes

Configure broker via these `.conf` files:

- `mosquitto_open.conf` – No auth, no TLS (for attack testing)
- `mosquitto_auth_only.conf` – Password + ACL, no TLS
- `mosquitto_tls_only.conf` – TLS only, allow anonymous
- `mosquitto_tls_auth.conf` – TLS + Auth + ACL (production secure)

## ⚙️ Environment Variables

All components use `.env` or default values:

```env
BROKER_ADDRESS=mqtt-broker
MQTT_USERNAME=user
MQTT_PASSWORD=pass
ENABLE_TLS=true
ENABLE_AUTH=true
ENABLE_HMAC=true
HMAC_SECRET=123iot45
```

## 🧪 Database Structure

| Table               | Description                            |
|---------------------|----------------------------------------|
| `sensor_data`       | Logs all sensor payloads               |
| `actuator_actions`  | Logs commands executed by actuators    |
| `anomaly_logs`      | Stores all flagged anomalies           |
| `registered_devices`| Tracks known/registered device IDs     |

## 🐳 Docker Setup (Example)

```bash
docker-compose up --build
```

Define services like:

```yaml
services:
  mqtt-broker:
    image: eclipse-mosquitto
    volumes:
      - ./mosquitto_tls_auth.conf:/mosquitto/config/mosquitto.conf
      - ./certs:/mosquitto/certs
    ports:
      - "8883:8883"

  hub:
    build: .
    environment:
      - ENABLE_TLS=true
      - ENABLE_AUTH=true
      - ENABLE_HMAC=true
    depends_on:
      - mqtt-broker
```

## 📦 Future Extensions

- 🔍 Real-time web dashboard for visualization
- 🧠 ML-based anomaly classification
- 📡 GNS3/NS-3 integration for networking scenarios
- 📱 Mobile alert system via SMS/email on anomaly

## 👨‍🔬 Authors & Credits

This project was designed for advanced IoT Security evaluation, as part of a graduate-level course on Cyber-Physical Systems Security.

## 📄 License

MIT License – Free to use, modify, and distribute.
