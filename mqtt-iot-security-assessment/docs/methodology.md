# Assessment Methodology

This assessment follows a lightweight version of the standard penetration-testing
lifecycle, scoped to a single MQTT-based smart-home system running in a
controlled lab.

## 1. Scope & rules of engagement
- **In scope:** one local Mosquitto broker and the simulated sensors in this
  repository, running on `localhost` / an isolated lab host.
- **Out of scope:** any system not owned by the tester. No scanning, sniffing,
  or publishing is performed against third-party or production infrastructure.
- **Goal:** evaluate authentication, authorization (topic permissions), and
  transport confidentiality; then design, apply, and validate mitigations.

## 2. Phases
| Phase | Activity | Tools |
|-------|----------|-------|
| Recon | Discover the broker, fingerprint version, enumerate open ports and any readable topics | `nmap` (+ `mqtt-subscribe`, `ssl-enum-ciphers` NSE) |
| Baseline capture | Record normal sensor traffic | `tcpdump` / `tshark`, Wireshark, MQTT Explorer |
| Testing | Attempt anonymous subscribe, unauthorized publish, actuator command injection, topic enumeration | custom Python PoCs (`src/attacks/`) |
| Analysis | Compare plaintext vs. TLS captures; confirm which data is exposed | Wireshark (`mqtt` display filter) |
| Remediation | Apply auth + topic ACL + TLS | Mosquitto config, OpenSSL |
| Validation | Re-run the same PoCs and confirm they now fail | `src/attacks/acl_test.py`, repeat captures |

## 3. Severity model
Findings are rated using **CVSS 3.1** base scores plus a short qualitative
rationale. For a home deployment, "impact" considers privacy (occupancy
inference from motion/temperature data), safety (actuator manipulation), and
integrity of automation decisions.

## 4. Evidence handling
All evidence (nmap output, pcaps, screenshots, tool logs) is stored under
`docs/evidence/` and referenced by filename in the report so each finding is
reproducible. Generated certificates, keys, and password files are **never**
committed (see `.gitignore`).

## 5. Reproducibility
Every finding in the report includes a copy-pasteable proof-of-concept command.
The same commands, re-run against the hardened broker, are used as the
validation evidence that the mitigation works.
