import os
from flask import Flask, request, render_template_string, render_template

app = Flask(__name__)

FLAG = os.environ.get("FLAG", "flag{test_signature_ssti}")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        signature = request.form.get("signature_text", "")
        
        # VULNERABILITY
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Preview</title>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500&display=swap" rel="stylesheet">
            <style>
                body { font-family: 'Poppins', sans-serif; background: #fafafa; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: #333; }
                .container { background: white; padding: 3rem; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 100%; max-width: 550px; text-align: center; }
                h1 { margin-top: 0; color: #4a4e69; font-weight: 500; font-size: 1.5rem; }
                .preview-box { background: #f8f9fa; border: 2px dashed #c9ada7; padding: 20px; border-radius: 8px; text-align: left; margin: 2rem 0; min-height: 100px; white-space: pre-wrap; font-family: monospace; }
                a.btn { display: inline-block; background: #9a8c98; color: white; border: none; padding: 12px 25px; border-radius: 8px; text-decoration: none; transition: background 0.3s; }
                a.btn:hover { background: #4a4e69; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Your Email Signature:</h1>
                <div class="preview-box">
                    {signature}
                </div>
                <a href="/" class="btn">Back</a>
            </div>
        </body>
        </html>
        """
        
        try:
            return render_template_string(template)
        except Exception as e:
            return f"Error: {e}"
            
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
