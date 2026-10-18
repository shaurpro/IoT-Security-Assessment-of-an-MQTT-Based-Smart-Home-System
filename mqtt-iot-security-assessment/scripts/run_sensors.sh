#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# run_sensors.sh — start both simulated sensors (temperature + motion).
#
# Baseline:
#   bash scripts/run_sensors.sh
#
# Hardened (each sensor uses its own credential + TLS):
#   MODE=hardened bash scripts/run_sensors.sh
#
# Ctrl-C stops both.
# -----------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${MODE:-baseline}"

pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if [[ "$MODE" == "hardened" ]]; then
    MQTT_TLS=1 MQTT_USERNAME=sensor_temp MQTT_PASSWORD='TempS3nsor!' \
        python3 "$ROOT/src/sensors/temperature_sensor.py" & pids+=($!)
    MQTT_TLS=1 MQTT_USERNAME=sensor_motion MQTT_PASSWORD='M0tionS3nsor!' \
        python3 "$ROOT/src/sensors/motion_sensor.py" & pids+=($!)
else
    python3 "$ROOT/src/sensors/temperature_sensor.py" & pids+=($!)
    python3 "$ROOT/src/sensors/motion_sensor.py" & pids+=($!)
fi

echo "[run_sensors] started in $MODE mode (PIDs: ${pids[*]}). Ctrl-C to stop."
wait
