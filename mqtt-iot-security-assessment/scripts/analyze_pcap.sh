#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# analyze_pcap.sh — quick command-line triage of a capture with tshark.
#
# Pulls out MQTT control packets and, for the baseline capture, shows that
# topic names and payloads are visible in cleartext. For the hardened capture
# it shows only TLS records (no readable MQTT layer).
#
# Usage:  bash scripts/analyze_pcap.sh docs/evidence/capture_baseline.pcap
# -----------------------------------------------------------------------------
set -euo pipefail

PCAP="${1:?usage: $0 <file.pcap>}"

if ! command -v tshark >/dev/null 2>&1; then
    echo "tshark not installed. sudo apt install tshark"
    exit 1
fi

echo "=== MQTT control packets (if any are readable) ==="
# msgtype 3 = PUBLISH. Shows topic and payload in plaintext when unencrypted.
tshark -r "$PCAP" -Y "mqtt" \
    -T fields -e frame.number -e mqtt.msgtype -e mqtt.topic -e mqtt.msg \
    2>/dev/null | head -n 40 || true

echo
echo "=== TLS records (present when traffic is encrypted) ==="
tshark -r "$PCAP" -Y "tls.record.content_type" \
    -T fields -e frame.number -e tls.record.content_type \
    2>/dev/null | head -n 10 || true

echo
echo "Interpretation:"
echo "  * Readable mqtt.topic / mqtt.msg above  => plaintext, confidentiality lost."
echo "  * Only TLS records, no mqtt fields       => encrypted, payloads protected."
