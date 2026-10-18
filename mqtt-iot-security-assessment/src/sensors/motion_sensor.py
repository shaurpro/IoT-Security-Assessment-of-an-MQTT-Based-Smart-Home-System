#!/usr/bin/env python3
"""
motion_sensor.py — simulated smart-home PIR motion sensor.

Publishes a JSON event to `home/hallway/motion` whenever "motion" is detected.
Detection is random (Poisson-ish) so the event stream is irregular, which makes
for interesting traffic to inspect.

Run (baseline, plaintext):
    python src/sensors/motion_sensor.py

Run (hardened, TLS + auth):
    MQTT_TLS=1 MQTT_USERNAME=sensor_motion MQTT_PASSWORD=M0tionS3nsor! \
        python src/sensors/motion_sensor.py
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import mqtt_settings, apply_client_security, describe, TOPIC_MOTION  # noqa: E402

DEVICE_ID = "motion-sensor-01"
TICK = float(os.environ.get("SENSOR_INTERVAL", "2"))
DETECT_PROB = 0.25  # chance of motion on each tick


def main() -> int:
    settings = mqtt_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
    apply_client_security(client, settings)

    print(f"[{DEVICE_ID}] connecting to {describe(settings)}")
    client.connect(settings["host"], settings["port"], keepalive=30)
    client.loop_start()

    try:
        while True:
            detected = random.random() < DETECT_PROB
            event = {
                "device_id": DEVICE_ID,
                "type": "motion",
                "detected": detected,
                "location": "hallway",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            payload = json.dumps(event)
            client.publish(TOPIC_MOTION, payload, qos=1, retain=False)
            marker = "MOTION" if detected else "clear"
            print(f"[{DEVICE_ID}] -> {TOPIC_MOTION}  {marker}")
            time.sleep(TICK)
    except KeyboardInterrupt:
        print(f"\n[{DEVICE_ID}] stopping")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
