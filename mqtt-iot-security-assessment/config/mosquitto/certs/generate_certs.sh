#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# generate_certs.sh — create a throwaway lab CA + server certificate for TLS.
#
# These certificates are for the LOCAL LAB ONLY. They are self-signed and must
# never be committed or reused. The .gitignore in this directory keeps the
# generated keys out of the repo.
#
# Usage:  bash config/mosquitto/certs/generate_certs.sh
# -----------------------------------------------------------------------------
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CERT_DIR"

DAYS=825
# Subject Alternative Name so clients can verify "localhost".
SAN="subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "[certs] generating CA..."
openssl req -new -x509 -days "$DAYS" -nodes \
    -keyout ca.key -out ca.crt \
    -subj "/C=US/O=MQTT-IoT-Lab/CN=MQTT-IoT-Lab-CA"

echo "[certs] generating server key + CSR..."
openssl req -new -nodes \
    -keyout server.key -out server.csr \
    -subj "/C=US/O=MQTT-IoT-Lab/CN=localhost"

echo "[certs] signing server certificate with lab CA..."
openssl x509 -req -in server.csr -days "$DAYS" \
    -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out server.crt \
    -extfile <(printf "%s" "$SAN")

chmod 644 ca.crt server.crt
chmod 600 ca.key server.key
rm -f server.csr ca.srl

echo "[certs] done. Files in $CERT_DIR:"
ls -1 ca.crt server.crt server.key
echo "[certs] (ca.key kept for reference; ca.crt is what clients trust)"
