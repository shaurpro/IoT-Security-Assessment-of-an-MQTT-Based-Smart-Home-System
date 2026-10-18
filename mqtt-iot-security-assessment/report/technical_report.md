# IoT Security Assessment — MQTT-Based Smart Home System

**Assessment type:** Controlled lab penetration test (self-assessment)
**Target:** Local Mosquitto MQTT broker + simulated temperature / motion sensors
**Tester:** _<your name>_
**Date:** _<YYYY-MM-DD>_
**Status template note:** Replace every _italic placeholder_ and every
`<...>` with your own measured results and screenshots before publishing.

---

## 1. Executive summary

A controlled security assessment was performed against a smart-home system
built on the MQTT protocol, comprising an MQTT broker and simulated temperature
and motion sensors. The assessment evaluated authentication, topic-level
authorization, and transport confidentiality.

In its baseline configuration the system allowed **anonymous access**, enforced
**no topic-level authorization**, and transmitted all data in **plaintext**.
This permitted an unauthenticated attacker on the network to (1) read all sensor
data — including motion events that reveal whether a home is occupied,
(2) inject forged sensor readings, and (3) publish actuator commands.

Three mitigations were implemented and validated: strong per-device
authentication, a least-privilege topic ACL, and TLS encryption. After
remediation, each proof-of-concept that previously succeeded was re-run and
**failed as expected**, confirming the controls are effective.

| # | Finding | Severity | Status after remediation |
|---|---------|----------|--------------------------|
| VULN-01 | Broker allows anonymous access (broken authentication) | High | Fixed — anonymous rejected |
| VULN-02 | No topic-level authorization (unauthorized publish) | High | Fixed — ACL enforced |
| VULN-03 | Plaintext transport (no TLS) exposes all data | High | Fixed — TLS 1.2 enforced |
| VULN-04 | Broker version/topics disclosed to unauthenticated recon | Low | Reduced — auth required to enumerate |

---

## 2. Scope and environment

- **Broker:** Eclipse Mosquitto 2.x (Docker image `eclipse-mosquitto:2`)
- **Devices:** `temp-sensor-01`, `motion-sensor-01` (Python, paho-mqtt)
- **Topics:**
  - `home/livingroom/temperature` — temperature readings
  - `home/hallway/motion` — motion events
  - `home/livingroom/thermostat/set` — actuator command
- **Network:** all components on `localhost` / isolated lab host
- **Tooling:** Nmap, Wireshark/tshark/tcpdump, MQTT Explorer, custom Python PoCs
- See `docs/methodology.md` for the full method and rules of engagement.

---

## 3. Findings

Each finding lists impact, a reproducible PoC, the evidence collected, a CVSS
3.1 vector, and the remediation applied.

### VULN-01 — Anonymous access / broken authentication  (High)

**Description.** The baseline broker is configured with `allow_anonymous true`
and no credentials. Any client that can reach TCP/1883 is treated as trusted.

**Impact.** Combined with VULN-02, an unauthenticated attacker gains full
read/write access to the smart-home message bus.

**Proof of concept.**
```bash
docker compose --profile baseline up -d
python src/sensors/temperature_sensor.py &   # produce some data
python src/attacks/eavesdrop.py --duration 10
```
Observed: the client connected with no credentials and received live readings.

**Evidence.** _`docs/evidence/eavesdrop_baseline.txt`, screenshot `<file>`._
Messages intercepted: _<N>_. Distinct topics exposed: _<list>_.

**CVSS 3.1:** _AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N_ → Base _<score>_ (High).
*(Adjust AV to N if your lab is reachable beyond the local segment.)*

**Remediation.** Set `allow_anonymous false` and require a password file;
issue a unique credential per device. See `config/mosquitto/hardened/`.

---

### VULN-02 — Missing topic-level authorization (unauthorized publish)  (High)

**Description.** No `acl_file` is configured, so every connected client may
publish and subscribe to every topic, including the actuator command topic.

**Impact.** An attacker can (a) inject forged temperature readings to corrupt
automation decisions, and (b) publish to `home/livingroom/thermostat/set` to
manipulate a physical device. Forged readings also impersonate a real
`device_id`, defeating naive source checks.

**Proof of concept.**
```bash
# Inject a fake reading
python src/attacks/spoof_publish.py --value 99.9
# Push an actuator command
python src/attacks/spoof_publish.py --command 30
```
Observed: both publishes were accepted; the monitoring subscriber received the
forged reading and the spoofed command.

**Evidence.** _`docs/evidence/spoof_baseline.txt`, subscriber log `<file>`._

**CVSS 3.1:** _AV:A/AC:L/PR:N/UI:N/S:C/C:L/I:H/A:L_ → Base _<score>_ (High).
Scope is Changed because the broker compromise affects downstream actuators.

**Remediation.** Add a least-privilege `aclfile` so each identity may only
touch the topics required for its role (sensors write only their own topic; the
hub reads sensors and writes the command topic). See
`config/mosquitto/hardened/aclfile`.

---

### VULN-03 — Plaintext transport exposes all data  (High)

**Description.** The baseline listener uses unencrypted MQTT on port 1883.
Topic names and JSON payloads are transmitted in cleartext.

**Impact.** A passive attacker with network visibility can read all sensor data
without ever connecting to the broker, and can harvest credentials if password
authentication were added without TLS.

**Proof of concept.**
```bash
sudo bash scripts/capture_traffic.sh baseline   # capture while sensors run
bash scripts/analyze_pcap.sh docs/evidence/capture_baseline.pcap
```
In Wireshark, apply the display filter `mqtt`; PUBLISH packets show the topic
and the JSON payload in plaintext.

**Evidence.** _`docs/evidence/capture_baseline.pcap` + screenshot `<file>`
showing a readable payload. Compare with `capture_hardened.pcap`, which shows
only TLS records._

**CVSS 3.1:** _AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N_ → Base _<score>_ (High).

**Remediation.** Enable a TLS listener on 8883, disable the plaintext listener,
and have clients verify the broker certificate against the lab CA. See
`config/mosquitto/hardened/mosquitto.conf` and
`config/mosquitto/certs/generate_certs.sh`.

---

### VULN-04 — Information disclosure to unauthenticated recon  (Low)

**Description.** During reconnaissance, Nmap's `mqtt-subscribe` script and
version detection reveal the broker version and, on the anonymous baseline,
readable topics.

**Impact.** Aids an attacker in fingerprinting and targeting the broker.

**Proof of concept.**
```bash
bash scripts/nmap_scan.sh 127.0.0.1
```

**Evidence.** _`docs/evidence/nmap_127_0_0_1.txt`._

**CVSS 3.1:** _AV:A/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N_ → Base _<score>_ (Low).

**Remediation.** Requiring authentication (VULN-01 fix) prevents anonymous
topic enumeration. Keep the broker patched; avoid exposing the broker beyond
the trusted network segment.

---

## 4. Remediation summary

| Control | Implementation | Validates which finding |
|---------|----------------|-------------------------|
| Strong authentication | `allow_anonymous false` + per-device password file | VULN-01, VULN-04 |
| Least-privilege authorization | Topic `aclfile` per identity | VULN-02 |
| Encrypted transport | TLS 1.2 listener on 8883, plaintext disabled | VULN-03 |

Apply with:
```bash
bash config/mosquitto/certs/generate_certs.sh
bash scripts/make_passwords.sh
docker compose --profile hardened up -d
```

---

## 5. Validation (post-remediation testing)

Each PoC was re-run against the hardened broker.

| Test | Baseline result | Hardened result |
|------|-----------------|-----------------|
| Anonymous connect | Allowed | Refused (not authorised) |
| Subscribe `home/#` anonymously | Full data leaked | Connection refused |
| Inject fake reading | Accepted | Denied by ACL |
| Publish actuator command (as sensor) | Accepted | Denied by ACL |
| Sniff payload in Wireshark | Cleartext JSON visible | Only TLS records |

Validation commands:
```bash
# should now FAIL to leak anything
python src/attacks/eavesdrop.py --duration 10

# ACL matrix for one identity (repeat per credential)
MQTT_TLS=1 MQTT_USERNAME=sensor_temp MQTT_PASSWORD='TempS3nsor!' \
    python src/attacks/acl_test.py
```

Paste the before/after tool output and Wireshark screenshots as evidence.

---

## 6. Recommendations (beyond the lab)

1. **Rotate and manage credentials** — unique secret per device, stored in a
   secrets manager, rotated on decommission.
2. **Consider mutual TLS (mTLS)** — client certificates (`require_certificate
   true`) so the broker also authenticates each device.
3. **Network segmentation** — place IoT devices on an isolated VLAN; never
   expose the broker directly to the internet.
4. **Monitoring** — alert on auth failures, unexpected publishers, and
   connections from new client IDs.
5. **Payload integrity** — sign or HMAC sensor payloads if automation makes
   safety-relevant decisions.

---

## Appendix A — Tooling
Nmap, Wireshark / tshark / tcpdump, MQTT Explorer, Eclipse Mosquitto,
Python 3 + paho-mqtt, OpenSSL.

## Appendix B — Evidence index
_List each file in `docs/evidence/` with a one-line description here._
