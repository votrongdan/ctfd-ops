# Packet Inspector 101 - Solution Writeup

## Analysis
The challenge provides a packet capture file `evidence.pcap`.

## Solution Steps
1. **Using Wireshark**:
   - Open `evidence.pcap` in Wireshark.
   - Apply display filter `http`.
   - Right-click the HTTP POST packet to `/api/v1/authenticate` and select **Follow -> TCP Stream**.
   - Read the payload containing: `{"username":"admin","secret_flag":"flag{...}"}`.

2. **Using strings / grep**:
   ```bash
   strings evidence.pcap | grep flag
   ```

3. **Automated Python**:
   Run `python3 solve.py <target_url>` to extract the flag pattern directly.
