# Evidence

Put your captured evidence here and reference it by filename in
`report/technical_report.md`. Suggested files:

| File | What it shows |
|------|---------------|
| `nmap_127_0_0_1.txt` | Recon: broker version, open ports, ciphers |
| `eavesdrop_baseline.txt` | Anonymous subscribe leaking all topics |
| `spoof_baseline.txt` | Unauthorized publish / command injection accepted |
| `capture_baseline.pcap` | Plaintext MQTT (readable topics + payloads) |
| `capture_hardened.pcap` | TLS-encrypted traffic (only TLS records) |
| `wireshark_plaintext.png` | Screenshot of a readable PUBLISH payload |
| `wireshark_tls.png` | Screenshot of encrypted records |
| `acl_matrix_sensor_temp.txt` | ACL test output proving least privilege |

Screenshots from MQTT Explorer showing the topic tree (before/after auth) also
make strong evidence.

> The `.gitignore` at the repo root ignores `*.pcap` by default so you don't
> accidentally commit large captures. Remove that line if you want to include a
> small sample capture in the repo, and make sure it contains no secrets.
