#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# capture_traffic.sh — capture MQTT traffic to a .pcap for Wireshark analysis.
#
# Run this while sensors + an attack script are active to collect the evidence
# that shows plaintext payloads (baseline) vs. encrypted TLS records (hardened).
#
# Usage:
#   sudo bash scripts/capture_traffic.sh baseline   # captures port 1883
#   sudo bash scripts/capture_traffic.sh hardened   # captures port 8883
#
# Needs tcpdump (or tshark) and root/pcap privileges. Captures on the loopback
# interface because the whole lab runs on localhost.
# -----------------------------------------------------------------------------
set -euo pipefail

MODE="${1:-baseline}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IFACE="${CAPTURE_IFACE:-lo}"

case "$MODE" in
  baseline) PORT=1883 ;;
  hardened) PORT=8883 ;;
  *) echo "usage: $0 [baseline|hardened]"; exit 1 ;;
esac

OUT="$ROOT/docs/evidence/capture_${MODE}.pcap"

if command -v tcpdump >/dev/null 2>&1; then
    echo "[capture] tcpdump on $IFACE port $PORT -> $OUT (Ctrl-C to stop)"
    tcpdump -i "$IFACE" -s 0 -w "$OUT" "tcp port $PORT"
elif command -v tshark >/dev/null 2>&1; then
    echo "[capture] tshark on $IFACE port $PORT -> $OUT (Ctrl-C to stop)"
    tshark -i "$IFACE" -f "tcp port $PORT" -w "$OUT"
else
    echo "Neither tcpdump nor tshark found. Install one, e.g. sudo apt install tcpdump"
    exit 1
fi

echo "[capture] saved -> $OUT"
echo "[capture] open in Wireshark and apply display filter:  mqtt"
