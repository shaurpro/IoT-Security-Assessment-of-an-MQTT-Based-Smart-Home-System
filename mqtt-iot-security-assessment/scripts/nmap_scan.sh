#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# nmap_scan.sh — reconnaissance step: discover and fingerprint the MQTT broker.
#
# Demonstrates the recon phase of the assessment. Saves output to docs/evidence
# so it can be referenced in the report.
#
# Usage:
#   bash scripts/nmap_scan.sh                 # scan localhost, default ports
#   bash scripts/nmap_scan.sh 192.168.1.50    # scan a specific lab host
#
# SCOPE: only scan hosts you own / are authorised to test.
# -----------------------------------------------------------------------------
set -euo pipefail

TARGET="${1:-127.0.0.1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/docs/evidence/nmap_${TARGET//[^0-9A-Za-z]/_}.txt"

if ! command -v nmap >/dev/null 2>&1; then
    echo "nmap is not installed. On Debian/Kali: sudo apt install nmap"
    exit 1
fi

echo "[nmap] scanning $TARGET for MQTT (1883) and MQTTS (8883)..."
# -sV service/version detection; mqtt-subscribe NSE grabs broker info/topics.
nmap -Pn -sV -p 1883,8883 \
     --script mqtt-subscribe,ssl-cert,ssl-enum-ciphers \
     "$TARGET" | tee "$OUT"

echo "[nmap] saved -> $OUT"
