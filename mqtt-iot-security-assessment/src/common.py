"""
common.py — shared configuration and helpers for the MQTT lab.

All components (sensors, subscriber, attack scripts) import from here so that a
single environment variable switches the whole lab between the *baseline*
(insecure) and *hardened* (TLS + auth) brokers.

Environment variables (all optional, sensible defaults for a local lab):
    MQTT_HOST       broker hostname            (default: localhost)
    MQTT_PORT       broker port                (default: 1883, or 8883 if MQTT_TLS=1)
    MQTT_TLS        "1" to enable TLS          (default: 0)
    MQTT_CA         path to CA certificate     (default: config/mosquitto/certs/ca.crt)
    MQTT_USERNAME   username for auth          (default: none)
    MQTT_PASSWORD   password for auth          (default: none)

Nothing here reaches outside the lab. The defaults point at localhost only.
"""

import os

DEFAULT_CA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "mosquitto", "certs", "ca.crt",
)


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")


def mqtt_settings() -> dict:
    """Resolve broker connection settings from the environment."""
    tls = env_bool("MQTT_TLS", False)
    port = int(os.environ.get("MQTT_PORT", 8883 if tls else 1883))
    return {
        "host": os.environ.get("MQTT_HOST", "localhost"),
        "port": port,
        "tls": tls,
        "ca": os.environ.get("MQTT_CA", DEFAULT_CA),
        "username": os.environ.get("MQTT_USERNAME") or None,
        "password": os.environ.get("MQTT_PASSWORD") or None,
    }


def apply_client_security(client, settings: dict) -> None:
    """Apply TLS and username/password to a paho-mqtt client based on settings."""
    if settings["username"]:
        client.username_pw_set(settings["username"], settings["password"])
    if settings["tls"]:
        # Verify the broker certificate against our lab CA.
        client.tls_set(ca_certs=settings["ca"])


def describe(settings: dict) -> str:
    mode = "TLS+AUTH" if settings["tls"] else "PLAINTEXT"
    auth = settings["username"] or "anonymous"
    return f"{settings['host']}:{settings['port']} [{mode}] as {auth}"


# Topic namespace used throughout the lab.
TOPIC_TEMPERATURE = "home/livingroom/temperature"
TOPIC_MOTION = "home/hallway/motion"
TOPIC_COMMAND = "home/livingroom/thermostat/set"   # actuator command topic
TOPIC_WILDCARD = "home/#"                           # everything under home/
