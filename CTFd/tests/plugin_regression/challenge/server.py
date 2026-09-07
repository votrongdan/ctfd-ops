import http.server
import os
import socketserver
import threading

class HTTP(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = (str(self.server.server_port) + ':' + os.environ['FLAG']).encode()
        self.send_response(200); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass

class TCP(socketserver.BaseRequestHandler):
    def handle(self): self.request.sendall(os.environ['FLAG'].encode())

for port in (8080, 8081):
    threading.Thread(target=http.server.ThreadingHTTPServer(('0.0.0.0', port), HTTP).serve_forever, daemon=True).start()
socketserver.ThreadingTCPServer.allow_reuse_address = True
socketserver.ThreadingTCPServer(('0.0.0.0', 2222), TCP).serve_forever()
