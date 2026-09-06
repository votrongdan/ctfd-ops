import os
import subprocess
import threading
from flask import Flask, request, render_template, make_response

app = Flask(__name__)

# FLAG: Retrieved from environment
FLAG = os.environ.get("FLAG", "flag{xss_test_flag_123}")

def run_bot(url):
    # Runs the selenium bot in the background
    subprocess.Popen(["python3", "bot.py", url])

@app.route("/")
def index():
    # CAREFUL: Do not change the parameter 'name' unless you update writeups and intended solutions
    name = request.args.get("name", "Guest")
    # VULNERABILITY: Reflected XSS. The 'name' parameter is not escaped.
    return render_template("index.html", name=name)

@app.route("/report", methods=["GET", "POST"])
def report():
    msg = ""
    if request.method == "POST":
        url = request.form.get("url", "")
        if url.startswith("http://") or url.startswith("https://"):
            # Start the bot
            threading.Thread(target=run_bot, args=(url,)).start()
            msg = "Admin is reviewing your URL!"
        else:
            msg = "Invalid URL. Must start with http:// or https://"
    
    return render_template("report.html", msg=msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
