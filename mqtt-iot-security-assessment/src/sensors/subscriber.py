#!/usr/bin/env python3
"""
subscriber.py — legitimate monitoring client (e.g. a smart-home hub/dashboard).

Subscribes to the home/# topic tree and prints every message it receives.
Used to prove the baseline setup works, and later to show that under the
hardened broker a client only sees the topics its ACL permits.

Run (baseline, plaintext, anonymous):
    python src/sensors/subscriber.py

Run (hardened, TLS + auth):
    MQTT_TLS=1 MQTT_USERNAME=dashboard MQTT_PASSWORD=D4shboard! \
        python src/sensors/subscriber.py
"""

import os
import sys

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import mqtt_settings, apply_client_security, describe, TOPIC_WILDCARD  # noqa: E402


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[subscriber] connected; subscribing to {TOPIC_WILDCARD}")
        client.subscribe(TOPIC_WILDCARD, qos=1)
    else:
        print(f"[subscriber] connection refused: {reason_code}")


def on_message(client, userdata, msg):
    print(f"[subscriber] {msg.topic}  {msg.payload.decode(errors='replace')}")


def main() -> int:
    settings = mqtt_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dashboard-hub")
    apply_client_security(client, settings)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[subscriber] connecting to {describe(settings)}")
    client.connect(settings["host"], settings["port"], keepalive=30)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[subscriber] stopping")
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
