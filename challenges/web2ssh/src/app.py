import os
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    return jsonify({
        "status": "online",
        "service": "Web2SSH Authentication Gateway",
        "ssh_user": "ctf",
        "ssh_pass": "web2ssh_access_2026",
        "hint": "Use these credentials to connect to the SSH service on port 22."
    })

if __name__ == "__main__":
    # Web service runs on port 8080 as required by the challenge spec
    app.run(host="0.0.0.0", port=8080)
