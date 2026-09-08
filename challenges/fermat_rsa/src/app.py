from flask import Flask, render_template, send_file, Response
import io
from generator import generate_challenge

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download")
def download():
    try:
        # Generate the dynamic ZIP containing the weak RSA parameters
        zip_bytes = generate_challenge()
        
        return send_file(
            io.BytesIO(zip_bytes),
            mimetype='application/zip',
            as_attachment=True,
            download_name='challenge.zip'
        )
    except Exception as e:
        return Response(f"Error generating challenge: {str(e)}", status=500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
