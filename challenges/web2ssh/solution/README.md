# Web2SSH Solution Guide

## Challenge Overview
- **Name:** Web2SSH
- **Category:** Web / SSH
- **Difficulty:** Beginner
- **Tested Features:** 
  1. Per-user isolated container environment
  2. Per-user dynamic flag injection via `$FLAG`
  3. Multi-service interaction (HTTP port 8080 + SSH port 22)
  4. Automatic container exposure via CTFd Whale

---

## Intended Solve Steps

1. **Step 1: Web Reconnaissance (HTTP Port 8080)**
   - Open browser or execute `curl http://<challenge_host>:<http_port>/`.
   - Inspect the HTML page source code or query `http://<challenge_host>:<http_port>/api/status`.
   - Find the SSH credentials:
     - **Username:** `ctf`
     - **Password:** `web2ssh_access_2026`

2. **Step 2: SSH Authentication (SSH Port 22)**
   - Connect to the container via SSH:
     ```bash
     ssh ctf@<challenge_host> -p <ssh_port>
     ```
   - Enter password: `web2ssh_access_2026`

3. **Step 3: Flag Extraction**
   - Once inside the container shell, read the flag file:
     ```bash
     cat /home/ctf/flag.txt
     ```
   - Submit the retrieved flag to CTFd.

---

## Running the Solver Script

```bash
python3 solution/solve.py <http_host> <http_port> <ssh_host> <ssh_port>
```

Example for local test container:
```bash
python3 solution/solve.py 127.0.0.1 8081 127.0.0.1 2221
```
