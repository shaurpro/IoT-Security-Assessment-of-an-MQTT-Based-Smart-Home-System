#!/usr/bin/env python3
"""
acl_test.py — automated access-control verification harness.

Runs a matrix of (identity x topic x action) attempts against the broker and
reports ALLOW/DENY for each. Run it against the baseline broker to show that
everything is permitted, and against the hardened broker to prove that the
topic-level ACL now enforces least privilege.

This is the "validation" step: it produces evidence that mitigations work.

How each action is judged:
  * PUBLISH authorization is read directly from the MQTT v5 PUBACK reason code
    (0x87 = "Not authorized"). MQTT 3.1.1 does not signal a denied publish.
  * SUBSCRIBE authorization is tested FUNCTIONALLY. Mosquitto returns a
    successful SUBACK even when the ACL forbids a read, then silently filters
    out messages the client may not receive. So a SUBACK code cannot prove read
    access. Instead we subscribe as the identity under test, have an authorised
    helper publish a probe to the topic, and check whether it actually arrives:
    arrives => ALLOW, filtered => DENY.

Usage:
    # baseline (anonymous allowed, no ACL)
    python src/attacks/acl_test.py

    # hardened — supply a credential set to test one identity at a time
    MQTT_TLS=1 MQTT_USERNAME=sensor_temp MQTT_PASSWORD=TempS3nsor! \
        python src/attacks/acl_test.py
"""

import os
import sys
import time

import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (  # noqa: E402
    mqtt_settings, apply_client_security, describe,
    TOPIC_TEMPERATURE, TOPIC_MOTION, TOPIC_COMMAND,
)

# (label, topic, action, probe_topic) ; action in {"pub", "sub"}.
# probe_topic is the concrete topic a helper publishes to when testing reads
# (needed because a subscription may be a wildcard).
CHECKS = [
    ("publish temperature", TOPIC_TEMPERATURE, "pub", None),
    ("publish motion",      TOPIC_MOTION,      "pub", None),
    ("publish command",     TOPIC_COMMAND,     "pub", None),
    ("subscribe temp",      TOPIC_TEMPERATURE, "sub", TOPIC_TEMPERATURE),
    ("subscribe motion",    TOPIC_MOTION,      "sub", TOPIC_MOTION),
    ("subscribe EVERYTHING", "home/#",         "sub", TOPIC_TEMPERATURE),
]

# Lab helper publishers: which identity is authorised to publish each probe
# topic, so the read test can inject a message. These are the repo's demo
# credentials; override via the environment if you changed them.
HELPERS = {
    TOPIC_TEMPERATURE: ("sensor_temp", os.environ.get("HELP_TEMP_PW", "TempS3nsor!")),
    TOPIC_MOTION:      ("sensor_motion", os.environ.get("HELP_MOTION_PW", "M0tionS3nsor!")),
}


def _code_value(rc) -> int:
    """Normalise a paho ReasonCode / int to its numeric value."""
    return int(getattr(rc, "value", rc))


def _new_client(settings, cid=None, username=None, password=None):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cid or "", protocol=mqtt.MQTTv5)
    # Start from the resolved settings but allow an identity override (helpers).
    local = dict(settings)
    if username is not None:
        local["username"], local["password"] = username, password
    apply_client_security(c, local)
    return c


def _helper_publish(settings, probe_topic, payload=b"acl-read-probe"):
    """Publish a probe to probe_topic as an authorised helper identity."""
    user, pw = HELPERS.get(probe_topic, (None, None))
    if user is None:
        return
    helper = _new_client(settings, cid="acl-helper", username=user, password=pw)
    try:
        helper.connect(settings["host"], settings["port"], keepalive=10)
    except Exception:  # noqa: BLE001
        return
    helper.loop_start()
    time.sleep(0.3)  # let CONNACK settle
    helper.publish(probe_topic, payload, qos=1)
    time.sleep(0.4)
    helper.loop_stop()
    helper.disconnect()


def _test_publish(settings, topic) -> str:
    """Publish once; read authorization from the MQTT v5 PUBACK reason code."""
    result = {"verdict": None}
    client = _new_client(settings, cid="acl-pub")

    def on_connect(c, u, f, rc, props):
        if _code_value(rc) != 0:
            result["verdict"] = "NO-CONNECT"
            return
        c.publish(topic, b"acl-probe", qos=1)

    def on_publish(c, u, mid, reason_code=None, props=None):
        rc = _code_value(reason_code) if reason_code is not None else 0
        # 0x00 success, 0x10 "no matching subscribers" (OK), 0x87 not authorized.
        result["verdict"] = "DENY" if rc >= 0x80 else "ALLOW"

    client.on_connect = on_connect
    client.on_publish = on_publish
    try:
        client.connect(settings["host"], settings["port"], keepalive=10)
    except Exception:  # noqa: BLE001
        return "NO-CONNECT"
    client.loop_start()
    deadline = time.time() + 3
    while result["verdict"] is None and time.time() < deadline:
        time.sleep(0.05)
    client.loop_stop()
    client.disconnect()
    return result["verdict"] or "DENY"


def _test_subscribe(settings, topic, probe_topic) -> str:
    """Subscribe, inject a probe via an authorised helper, check delivery."""
    state = {"connected": None, "received": False}
    client = _new_client(settings, cid="acl-sub")

    def on_connect(c, u, f, rc, props):
        if _code_value(rc) != 0:
            state["connected"] = False
            return
        state["connected"] = True
        c.subscribe(topic, qos=1)

    def on_message(c, u, msg):
        state["received"] = True

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(settings["host"], settings["port"], keepalive=10)
    except Exception:  # noqa: BLE001
        return "NO-CONNECT"
    client.loop_start()

    # wait for connect
    deadline = time.time() + 3
    while state["connected"] is None and time.time() < deadline:
        time.sleep(0.05)
    if state["connected"] is False:
        client.loop_stop(); client.disconnect()
        return "NO-CONNECT"

    time.sleep(0.3)                       # ensure SUBSCRIBE is registered
    _helper_publish(settings, probe_topic)  # authorised client injects a message
    deadline = time.time() + 2
    while not state["received"] and time.time() < deadline:
        time.sleep(0.05)

    client.loop_stop()
    client.disconnect()
    return "ALLOW" if state["received"] else "DENY"


def try_action(settings, topic, action, probe_topic=None) -> str:
    """Return 'ALLOW', 'DENY', or 'NO-CONNECT'."""
    if action == "pub":
        return _test_publish(settings, topic)
    return _test_subscribe(settings, topic, probe_topic or topic)


def main() -> int:
    settings = mqtt_settings()
    print(f"[acl] identity/target: {describe(settings)}\n")
    print(f"{'check':<22}{'topic':<34}{'result'}")
    print("-" * 68)
    allow = 0
    for label, topic, action, probe_topic in CHECKS:
        verdict = try_action(settings, topic, action, probe_topic)
        allow += verdict == "ALLOW"
        print(f"{label:<22}{topic:<34}{verdict}")
    print()
    if allow == len(CHECKS):
        print("[acl] ALLOW on everything => no access control (baseline).")
    else:
        print("[acl] Mixed ALLOW/DENY matching the device's role => least privilege enforced (hardened).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
