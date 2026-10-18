# IoT Security Assessment of an MQTT-Based Smart Home System

A hands-on, reproducible penetration-testing lab that assesses the security of a
smart-home system built on **MQTT**. It stands up an MQTT broker and simulated
temperature / motion sensors, demonstrates real attacks against an insecure
baseline (anonymous access, no topic permissions, plaintext traffic), then
applies and **validates** mitigations (authentication, topic-level ACLs, TLS).

> **Ethics & scope.** Everything here runs locally against a broker and devices
> you own. The attack scripts default to `localhost` and are meant for this
> self-contained lab only. Do not point them at systems you are not authorised
> to test.

**Stack:** Python (paho-mqtt) · Eclipse Mosquitto · Nmap · Wireshark / tshark ·
MQTT Explorer · OpenSSL · Docker · Linux

---

## What this project demonstrates

- Building a controlled IoT test environment (broker + simulated sensors).
- Finding and proving three classes of MQTT misconfiguration:
  - **Broken authentication** — anonymous clients accepted.
  - **Missing authorization** — any client can publish/subscribe to any topic,
    including actuator commands.
  - **No transport encryption** — topics and payloads readable in Wireshark.
- Comparing plaintext vs. TLS traffic captures.
- Implementing fixes and re-running the same proofs-of-concept to show they now
  fail — i.e., evidence the controls actually work.
- Writing it all up in a structured technical report with severity ratings,
  reproducible PoCs, and remediation steps.

---

## Repository layout

```
.
├── README.md
├── requirements.txt
├── docker-compose.yml           # baseline + hardened broker profiles
├── Makefile                     # one-word shortcuts for every step
├── config/mosquitto/
│   ├── baseline/mosquitto.conf  # intentionally insecure target
│   ├── hardened/                # mosquitto.conf + aclfile (remediation)
│   └── certs/generate_certs.sh  # throwaway lab TLS CA + server cert
├── src/
│   ├── common.py                # shared broker settings (env-driven)
│   ├── sensors/                 # temperature_sensor, motion_sensor, subscriber
│   └── attacks/                 # eavesdrop, spoof_publish, acl_test (PoCs)
├── scripts/                     # nmap scan, traffic capture, pcap analysis, etc.
├── docs/
│   ├── methodology.md           # test methodology & rules of engagement
│   └── evidence/                # put nmap output, pcaps, screenshots here
└── report/technical_report.md   # the deliverable report (fill in your results)
```

---

## Prerequisites

- **Docker** (for the broker) — or a locally installed Mosquitto.
- **Python 3.9+**
- **Nmap**, **Wireshark/tshark** or **tcpdump**, and optionally **MQTT Explorer**
  (GUI) for a nicer view of the topic tree.
- Linux is assumed (Kali works well); macOS is fine too.

```bash
pip install -r requirements.txt     # or: make install
```

---

## Walkthrough

The whole assessment is five stages. Each maps to a section of the report.

### 1. Baseline (insecure) broker + sensors

```bash
make baseline            # starts Mosquitto on plaintext 1883
make sensors             # runs temperature + motion sensors
# in another terminal, watch legitimate traffic:
python src/sensors/subscriber.py
```

### 2. Recon

```bash
make acl-test            # or: bash scripts/nmap_scan.sh 127.0.0.1
bash scripts/nmap_scan.sh 127.0.0.1
```
Nmap fingerprints the broker and (on the anonymous baseline) can enumerate
topics. Output is saved under `docs/evidence/`.

### 3. Attack the baseline

```bash
# Confidentiality: read everything with no credentials
python src/attacks/eavesdrop.py --duration 10

# Integrity: inject a fake reading, then a spoofed actuator command
python src/attacks/spoof_publish.py --value 99.9
python src/attacks/spoof_publish.py --command 30
```

### 4. Capture & compare traffic

```bash
sudo bash scripts/capture_traffic.sh baseline   # Ctrl-C after a few seconds
bash scripts/analyze_pcap.sh docs/evidence/capture_baseline.pcap
```
Open the pcap in Wireshark, filter on `mqtt`, and you'll see topic names and
JSON payloads in cleartext. Save a screenshot as evidence.

### 5. Remediate, then validate

```bash
make certs               # generate lab TLS certificates
make passwords           # build the per-device password file
make down && make hardened   # start the TLS + auth + ACL broker on 8883

# sensors now authenticate over TLS:
MODE=hardened make sensors

# re-run the attacks — they should now FAIL:
python src/attacks/eavesdrop.py --duration 10          # refused / no data
MQTT_TLS=1 MQTT_USERNAME=sensor_temp MQTT_PASSWORD='TempS3nsor!' \
    python src/attacks/acl_test.py                     # least-privilege matrix

# capture again — now only TLS records are visible:
sudo bash scripts/capture_traffic.sh hardened
bash scripts/analyze_pcap.sh docs/evidence/capture_hardened.pcap
```

Record the before/after results in `report/technical_report.md`.

---

## Configuration (how components find the broker)

All clients read these environment variables (see `src/common.py`):

| Variable | Default | Meaning |
|----------|---------|---------|
| `MQTT_HOST` | `localhost` | broker host |
| `MQTT_PORT` | `1883` (or `8883` if TLS) | broker port |
| `MQTT_TLS` | `0` | `1` to use TLS |
| `MQTT_CA` | `config/mosquitto/certs/ca.crt` | CA to verify the broker |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | _unset_ | credentials for the hardened broker |

Lab demo credentials (hardened broker): `sensor_temp`, `sensor_motion`,
`dashboard`, `thermostat` — see `scripts/make_passwords.sh`. These are
**demo-only**; change them for anything beyond the lab.

---

## The report

`report/technical_report.md` is the main written deliverable. It contains the
methodology, four findings (with CVSS 3.1 vectors, reproducible PoCs, and
remediation), a remediation summary, and a validation table. It is written as a
**template** — replace the italic placeholders with your own measured results
and screenshots so the numbers are genuinely yours.

---

## Suggested résumé bullets

Use these **only after** you've actually run the lab and filled in your findings:

**IoT Security Assessment of an MQTT-Based Smart Home System** — *Python, MQTT,
Wireshark, Nmap*
- Built a controlled IoT test environment with simulated sensors and an MQTT
  broker to assess authentication, access-control, and network-communication
  security.
- Analysed MQTT traffic and evaluated security misconfigurations through
  controlled tests, documenting reproducible evidence and potential impact.
- Implemented and validated security mitigations — topic-level access controls
  and encrypted communication — and documented findings in a technical
  assessment report.

---

## License

MIT — see [LICENSE](LICENSE).
