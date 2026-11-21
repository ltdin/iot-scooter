# COSC2790-Assignment4-2026a-group8

## Phase 1 - Master Pi Core Scaffold

This repository is structured around the Scooter Share Platform assignment.
The current implementation starts the Master Pi backend skeleton for Person A.

### Main Folders

```text
master/
  app.py                 Flask REST API entrypoint
  socket_server.py       Socket server for Agent Pi request/response messages
  mqtt_server.py         MQTT server-side for receiving/sending data from/to scooter units
  api/                   REST API routes
  db/                    Cloud MySQL connection and schema files
  repositories/          Database access layer
  services/              Business logic layer
  utils/                 Validation, responses, constants, password helpers

agent/
  socket_client.py       Helper used by Agent Pis to send requests to Master Pi
  mqtt_client.py         MQTT client-side for scooters to send/receive data to/from the server-side

shared/
  socket_messages.py     Shared socket message builder
```

### Create virtual environment

```bash
python -m venv .venv
. .venv/bin/activate
```

### Run Master API

```bash
python -m master.app
```

Health check:

```text
GET http://localhost:5000/health
```

### Run Master Socket Server

```bash
python -m master.socket_server
```

Default socket endpoint:

```text
0.0.0.0:9000
```

### Run MQTT
Intall packages

```bash
sudo apt install -y mosquitto mosquitto-clients
sudo apt install python3-paho-mqtt python3-rsa
```

```bash
. .venv/bin/activate
pip install paho-mqtt rsa
```

Run Broker

```bash
sudo systemctl stop mosquitto
mosquitto
```

Run server-side MQTT

```bash
. .venv/bin/activate
python -m master.mqtt_server
```

Run client-side MQTT

 - Make sure to exit your virtual environment first if you are in one
```bash
deactivate
```

```bash
python -m agent.mqtt_client
```

Run crash/theft detection

```bash
python3 -m agent.ap_safety_runner --scooter-id <scooter_id> --mp-base-url http://<AP_ip>:5000
```

### Next Phase

Phase 2 connects this scaffold to the cloud MySQL database and replaces the repository placeholders with real CRUD operations.

### Cloud SQL Setup

Create a `.env` file from `.env.example` and fill in the Cloud SQL values:

```text
DB_HOST=34.87.82.162
DB_PORT=3306
DB_NAME=scooter_share
DB_USER=scooter_user
DB_PASSWORD=your_password
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Apply database schema and seed data:

```bash
python -m master.db.init_db
```

Seed accounts:

```text
admin / Admin123!
engineer1 / Engineer123!
alice / Alice123!
bob / Bob123!
```
