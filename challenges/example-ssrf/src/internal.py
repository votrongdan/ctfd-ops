import os
from flask import Flask
app = Flask(__name__)
FLAG = os.environ.get("FLAG", "flag{test_ssrf_internal_flag}")
@app.route("/")
def index():
    return "Internal Admin Dashboard"
@app.route("/secret")
def secret():
    return f"Admin Secret: {FLAG}"
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
