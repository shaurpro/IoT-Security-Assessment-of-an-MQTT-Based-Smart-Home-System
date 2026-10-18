#!/usr/bin/env python3
"""
temperature_sensor.py — simulated smart-home temperature sensor.

Publishes a JSON reading to `home/livingroom/temperature` every few seconds.
Readings follow a slow random walk around a target temperature so captured
traffic looks realistic in Wireshark / MQTT Explorer.

Run (baseline, plaintext):
    python src/sensors/temperature_sensor.py

Run (hardened, TLS + auth):
    MQTT_TLS=1 MQTT_USERNAME=sensor_temp MQTT_PASSWORD=TempS3nsor! \
        python src/sensors/temperature_sensor.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import mqtt_settings, apply_client_security, describe, TOPIC_TEMPERATURE  # noqa: E402

DEVICE_ID = "temp-sensor-01"
INTERVAL = float(os.environ.get("SENSOR_INTERVAL", "3"))
TARGET_C = 21.5


def make_reading(state: dict) -> dict:
    # Gentle random walk, clamped to a plausible indoor range.
    state["value"] += random.uniform(-0.3, 0.3)
    state["value"] = max(16.0, min(28.0, state["value"]))
    return {
        "device_id": DEVICE_ID,
        "type": "temperature",
        "unit": "C",
        "value": round(state["value"], 2),
        "battery": state["battery"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    settings = mqtt_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
    apply_client_security(client, settings)

    print(f"[{DEVICE_ID}] connecting to {describe(settings)}")
    client.connect(settings["host"], settings["port"], keepalive=30)
    client.loop_start()

    state = {"value": TARGET_C, "battery": 100}
    try:
        while True:
            reading = make_reading(state)
            payload = json.dumps(reading)
            info = client.publish(TOPIC_TEMPERATURE, payload, qos=1, retain=True)
            info.wait_for_publish(timeout=5)
            print(f"[{DEVICE_ID}] -> {TOPIC_TEMPERATURE}  {payload}")
            # Slowly drain the battery so there is some varying state to watch.
            if random.random() < 0.05 and state["battery"] > 1:
                state["battery"] -= 1
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[{DEVICE_ID}] stopping")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
