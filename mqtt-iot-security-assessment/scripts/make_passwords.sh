#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# make_passwords.sh — build the hashed Mosquitto password file for the four
# lab identities used in the hardened broker.
#
# Requires the `mosquitto_passwd` tool (ships with mosquitto).
# If you run the broker via Docker, you can also generate it inside the
# container — see README "Hardened broker".
#
# Usage:  bash scripts/make_passwords.sh
# Output: config/mosquitto/hardened/passwordfile
# -----------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PWFILE="$ROOT/config/mosquitto/hardened/passwordfile"

# identity:password pairs (lab-only demo credentials).
declare -A CREDS=(
    [sensor_temp]="TempS3nsor!"
    [sensor_motion]="M0tionS3nsor!"
    [dashboard]="D4shboard!"
    [thermostat]="Th3rmostat!"
)

if ! command -v mosquitto_passwd >/dev/null 2>&1; then
    echo "mosquitto_passwd not found on PATH."
    echo "Install mosquitto, or generate the file inside the Docker container:"
    echo "  docker run --rm -it -v \"$ROOT/config/mosquitto/hardened:/h\" eclipse-mosquitto:2 \\"
    echo "    sh -c 'for u in sensor_temp sensor_motion dashboard thermostat; do \\"
    echo "      mosquitto_passwd -b /h/passwordfile \$u changeme; done'"
    exit 1
fi

rm -f "$PWFILE"
first=1
for user in "${!CREDS[@]}"; do
    if [[ $first -eq 1 ]]; then
        mosquitto_passwd -c -b "$PWFILE" "$user" "${CREDS[$user]}"
        first=0
    else
        mosquitto_passwd -b "$PWFILE" "$user" "${CREDS[$user]}"
    fi
done

chmod 600 "$PWFILE"
echo "[passwd] wrote $PWFILE for: ${!CREDS[*]}"
