import os
from flask import Flask, request, render_template

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'uploads/'

FLAG = os.environ.get("FLAG", "flag{test_resume_upload}")

@app.route("/", methods=["GET", "POST"])
def index():
    msg = ""
    if request.method == "POST":
        if 'resume' not in request.files:
            msg = "No file part"
        else:
            file = request.files['resume']
            if file.filename == '':
                msg = "No selected file"
            else:
                # VULNERABILITY
                filename = file.filename
                try:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    msg = f"Resume '{filename}' received. We will review it shortly."
                except Exception as e:
                    msg = f"Error: {e}"
                    
    return render_template("index.html", msg=msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
