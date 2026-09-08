import os
import subprocess
from flask import Flask, request, render_template, send_file, jsonify
from build_vault import build

app = Flask(__name__)

# Compile vault binary dynamically on startup
build()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download/vault")
def download():
    filepath = os.path.join(os.path.dirname(__file__), "vault")
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name="vault")
    return "Vault binary missing", 404

@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.get_json(force=True, silent=True) or {}
    passcode = data.get("passcode", "")
    
    vault_path = os.path.join(os.path.dirname(__file__), "vault")
    if not os.path.exists(vault_path):
        return jsonify({"error": "Binary missing"}), 500

    try:
        res = subprocess.run([vault_path, passcode], capture_output=True, text=True, timeout=5)
        return jsonify({
            "returncode": res.returncode,
            "stdout": res.stdout,
            "stderr": res.stderr
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
