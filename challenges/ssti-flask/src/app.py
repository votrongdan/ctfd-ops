import os
from flask import Flask, request, render_template_string, render_template

app = Flask(__name__)

# FLAG is loaded into the environment by Whale
# Attackers will need to extract it via SSTI -> RCE -> env
FLAG = os.environ.get("FLAG", "flag{ssti_test_flag_999}")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "Guest")
        
        # VULNERABILITY: User input is concatenated directly into the template string.
        # This causes Jinja2 to evaluate the user input as code (SSTI).
        template = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Greeting</title></head>
        <body>
            <h1>Hello, {name}!</h1>
            <a href="/">Go back</a>
        </body>
        </html>
        """
        
        try:
            return render_template_string(template)
        except Exception as e:
            return f"Error rendering template: {e}"
            
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
