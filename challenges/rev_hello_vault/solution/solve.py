import requests
import re
import sys
import subprocess

def solve(target_url):
    download_url = target_url.rstrip('/') + '/download/vault'
    print(f"[*] Downloading binary from {download_url}...")
    res = requests.get(download_url)
    if res.status_code != 200:
        print(f"[-] Failed to download binary: {res.status_code}")
        return False

    binary_data = res.content
    
    # Simple extraction method: read binary bytes and search for byte pattern or reverse XOR key 0x42
    # Since the flag starts with "flag{" -> XOR with 0x42 = 'f'^0x42 = 0x24, 'l'^0x42 = 0x2e, 'a'^0x42 = 0x23, 'g'^0x42 = 0x25, '{'^0x42 = 0x39
    header_pattern = bytes([ord('f') ^ 0x42, ord('l') ^ 0x42, ord('a') ^ 0x42, ord('g') ^ 0x42, ord('{') ^ 0x42])
    idx = binary_data.find(header_pattern)
    
    if idx != -1:
        # Read until closing brace XORed: '}' ^ 0x42 = 0x3f
        end_idx = binary_data.find(bytes([ord('}') ^ 0x42]), idx)
        if end_idx != -1:
            encoded_flag = binary_data[idx:end_idx+1]
            decoded_flag = "".join(chr(b ^ 0x42) for b in encoded_flag)
            print(f"[+] Found Flag: {decoded_flag}")
            
            # Verify with API
            verify_url = target_url.rstrip('/') + '/api/verify'
            v_res = requests.post(verify_url, json={"passcode": decoded_flag})
            if "ACCESS GRANTED" in v_res.json().get("stdout", ""):
                print("[+] Verified Flag with Target Server!")
                return True
    
    print("[-] Flag pattern not found automatically in binary")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8002"
    success = solve(target)
    sys.exit(0 if success else 1)
