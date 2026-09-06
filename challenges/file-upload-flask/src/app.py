import os
from flask import Flask, request, render_template

app = Flask(__name__)
# Ensure templates are reloaded immediately so our exploit works
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = 'uploads/'

# FLAG is loaded into the environment by Whale
FLAG = os.environ.get("FLAG", "flag{upload_test_flag_999}")

@app.route("/", methods=["GET", "POST"])
def index():
    msg = ""
    if request.method == "POST":
        if 'file' not in request.files:
            msg = "No file part"
        else:
            file = request.files['file']
            if file.filename == '':
                msg = "No selected file"
            else:
                # VULNERABILITY: Missing werkzeug.utils.secure_filename()
                # An attacker can upload a file named "../templates/index.html"
                filename = file.filename
                
                try:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    msg = f"File {filename} successfully uploaded!"
                except Exception as e:
                    msg = f"Error saving file: {e}"
                    
    return render_template("index.html", msg=msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
