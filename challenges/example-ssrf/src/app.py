import requests
from flask import Flask, request, render_template
app = Flask(__name__)
@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    if request.method == "POST":
        url = request.form.get("url", "")
        if url:
            try:
                # VULNERABILITY: Fetching user-provided URL without validation
                resp = requests.get(url, timeout=3)
                result = resp.text
            except Exception as e:
                error = str(e)
    return render_template("index.html", result=result, error=error)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
