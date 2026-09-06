import os
import subprocess
import threading
from flask import Flask, request, render_template

app = Flask(__name__)

FLAG = os.environ.get("FLAG", "flag{test_helpdesk_xss}")

def run_bot(url):
    subprocess.Popen(["python3", "bot.py", url])

@app.route("/")
def index():
    ticket_id = request.args.get("ticket_id", "TKT-001")
    return render_template("index.html", ticket_id=ticket_id)

@app.route("/support", methods=["GET", "POST"])
def support():
    msg = ""
    if request.method == "POST":
        url = request.form.get("url", "")
        if url.startswith("http://") or url.startswith("https://"):
            threading.Thread(target=run_bot, args=(url,)).start()
            msg = "Support staff is reviewing your ticket link!"
        else:
            msg = "Invalid URL."
    return render_template("support.html", msg=msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
