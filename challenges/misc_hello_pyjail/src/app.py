import os
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Write dynamic flag to /flag.txt
def init_flag():
    flag = os.environ.get("FLAG", "flag{pyj41l_b3g1nn3r_3sc4p3_79c1a4}")
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

BLACK_LIST = ["import", "os", "system", "eval", "exec", "open", "read", "subprocess"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "").strip()

    if not code:
        return jsonify({"error": "No Python code provided"}), 400

    # Check blacklist
    for bad in BLACK_LIST:
        if bad in code.lower():
            return jsonify({"error": f"Security Alert: Forbidden keyword '{bad}' detected in code string!"}), 403

    try:
        # Evaluate user expression
        result = eval(code, {"__builtins__": __builtins__})
        return jsonify({"result": str(result)})
    except Exception as e:
        return jsonify({"error": f"Execution Error: {type(e).__name__}: {str(e)}"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
