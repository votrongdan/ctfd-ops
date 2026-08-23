import requests
import re
import sys

def solve(target_url):
    pcap_url = target_url.rstrip('/') + '/download/evidence.pcap'
    print(f"[*] Downloading PCAP file from {pcap_url}...")
    res = requests.get(pcap_url)
    
    if res.status_code != 200:
        print(f"[-] Download failed with status {res.status_code}")
        return False

    content = res.content
    match = re.search(rb'flag\{[a-zA-Z0-9_]+\}', content)
    if match:
        flag = match.group(0).decode('utf-8')
        print(f"[+] Found Flag in PCAP: {flag}")
        return True

    # Alternatively test via online string search API
    search_url = target_url.rstrip('/') + '/api/search_pcap?query=flag'
    s_res = requests.get(search_url)
    if s_res.status_code == 200:
        results = s_res.json().get("results", [])
        for r in results:
            match = re.search(r'flag\{[a-zA-Z0-9_]+\}', r)
            if match:
                print(f"[+] Found Flag via Search API: {match.group(0)}")
                return True

    print("[-] Flag not found in PCAP")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8003"
    success = solve(target)
    sys.exit(0 if success else 1)
