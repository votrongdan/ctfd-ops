import os
from flask import Flask, request, render_template, Response

app = Flask(__name__)

def get_flag():
    return os.environ.get("FLAG", "flag{0s1n7_r3c0n_d1sc0v3ry_m4st3r_17a89b}").strip()

@app.route("/")
def index():
    resp = Response(render_template("index.html"))
    resp.headers["X-Developer-Contact"] = "j_miller@aegiscorp.internal"
    return resp

@app.route("/robots.txt")
def robots():
    content = """User-agent: *
Disallow: /backup_archives/
Disallow: /dev_notes.txt
Disallow: /api/debug
"""
    return Response(content, mimetype="text/plain")

@app.route("/dev_notes.txt")
def dev_notes():
    content = """=== Aegis Internal System Notes ===
Author: J. Miller (Lead System Engineer)
Date: 2026-04-12

Task List:
[x] Migrate user authentication service to TLS 1.3
[x] Sanitize public endpoint responses
[ ] Purge configuration backups from public web server root!
    Reminder: /backup_archives/sys_config.bak contains legacy environment variables.

For inquiries, contact j_miller@aegiscorp.internal
"""
    return Response(content, mimetype="text/plain")

@app.route("/backup_archives/sys_config.bak")
def sys_config_bak():
    flag = get_flag()
    content = f"""# Aegis Corporation System Configuration Backup
[SYSTEM]
APP_NAME = Aegis Intranet Portal
ENVIRONMENT = Production
PRIMARY_ADMIN = j_miller@aegiscorp.internal
DEPLOY_REGION = us-east-1

[SECURITY]
SECRET_KEY = 3f9a12c8b0e74f6d
FLAG = {flag}
"""
    return Response(content, mimetype="text/plain")

@app.route("/api/debug")
def api_debug():
    return Response('{"status": "ok", "debug": false, "hint": "Check /dev_notes.txt or /robots.txt"}', mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
