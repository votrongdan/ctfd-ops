import os
from flask import Flask, request, render_template, abort

app = Flask(__name__)

EXHIBITS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exhibits')

# Write the flag to /flag.txt at startup from the FLAG env var
def init_flag():
    flag = os.environ.get("FLAG", "flag{lfi_s1mpl3_tr4v3rsal_8b9c1d}")
    try:
        with open("/flag.txt", "w") as f:
            f.write(flag)
    except Exception as e:
        # Fallback inside the app folder for local manual execution
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag.txt"), "w") as f:
                f.write(flag)
        except:
            pass

init_flag()

# Exhibit metadata
EXHIBITS = {
    "quantum_core.txt": {
        "title": "Quantum Reactor Core",
        "summary": "Supercritical zero-point energy containment unit designed for deep space travel.",
        "icon": "⚛️"
    },
    "aether_sails.txt": {
        "title": "Aether Solar Sails",
        "summary": "Lightweight reflective membranes harvesting solar winds and cosmic radiation.",
        "icon": "⛵"
    },
    "chrono_dial.txt": {
        "title": "Chrono Resonance Dial",
        "summary": "A complex temporal shifting apparatus adjusting local spacetime coordinates.",
        "icon": "⏳"
    }
}

@app.route("/")
def index():
    filename = request.args.get("file", "")
    content = ""
    error = ""
    selected_exhibit = None

    if filename:
        # VULNERABLE PATH CONCATENATION: Directly joining user input
        filepath = os.path.join(EXHIBITS_DIR, filename)
        try:
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    content = f.read()
                
                # Check if it matches a known exhibit for UI enhancement
                if filename in EXHIBITS:
                    selected_exhibit = EXHIBITS[filename]
                else:
                    selected_exhibit = {
                        "title": filename,
                        "summary": "External system catalog or data source.",
                        "icon": "📄"
                    }
            else:
                error = f"Error: The requested file '{filename}' could not be located in the catalog archives."
        except Exception as e:
            error = f"System Error: {str(e)}"

    return render_template(
        "index.html",
        exhibits=EXHIBITS,
        selected_exhibit=selected_exhibit,
        content=content,
        error=error,
        filename=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
