# Aegis Recon 101 - Solution Writeup

## Analysis
This challenge demonstrates basic OSINT web reconnaissance techniques.

## Solution Steps
1. **Inspect `robots.txt`**:
   Navigate to `http://<target_host>/robots.txt` to find disallowed paths:
   - `/dev_notes.txt`
   - `/backup_archives/`

2. **Read Developer Notes**:
   Navigate to `http://<target_host>/dev_notes.txt` to read J. Miller's notes, which mention that `/backup_archives/sys_config.bak` contains legacy environment variables.

3. **Download Configuration Backup**:
   Navigate to `http://<target_host>/backup_archives/sys_config.bak`.
   Extract `FLAG = flag{0s1n7_r3c0n_d1sc0v3ry_m4st3r_17a89b}`!
