import os
import subprocess
import base64
from flask import Flask, request, render_template, send_file, jsonify

app = Flask(__name__)

# Write flag to /flag.txt on startup
def init_flag():
    flag = os.environ.get("FLAG", "flag{pwn_b3g1nn3r_buff3r_0v3rfl0w_38a91c}")
    try:
        with open("/flag.txt", "w") as f:
            f.write(flag if flag.endswith("\n") else flag + "\n")
    except Exception as e:
        try:
            with open("flag.txt", "w") as f:
                f.write(flag if flag.endswith("\n") else flag + "\n")
        except:
            pass

init_flag()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    if filename in ["chall", "chall.c"]:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    return "File not found", 404

@app.route("/api/interact", methods=["POST"])
def interact():
    data = request.get_json(force=True, silent=True) or {}
    payload_b64 = data.get("payload_b64", "")
    
    if not payload_b64:
        return jsonify({"error": "No payload_b64 provided"}), 400

    try:
        raw_payload = base64.b64decode(payload_b64)
    except Exception as e:
        return jsonify({"error": f"Invalid base64 payload: {str(e)}"}), 400

    chall_path = os.path.join(os.path.dirname(__file__), "chall")
    if not os.path.exists(chall_path):
        return jsonify({"error": "Binary executable missing"}), 500

    try:
        p = subprocess.Popen(
            [chall_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(input=raw_payload, timeout=5)
        output = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        p.kill()
        return jsonify({"error": "Process timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
