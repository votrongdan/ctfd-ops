import os
from flask import Flask, request, render_template, send_file, jsonify
from generate_pcap import build_pcap

app = Flask(__name__)

# Build evidence.pcap dynamically on startup
build_pcap()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download/evidence.pcap")
def download():
    filepath = os.path.join(os.path.dirname(__file__), "evidence.pcap")
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name="evidence.pcap")
    return "PCAP file missing", 404

@app.route("/api/search_pcap", methods=["GET"])
def search_pcap():
    filepath = os.path.join(os.path.dirname(__file__), "evidence.pcap")
    if not os.path.exists(filepath):
        return jsonify({"error": "PCAP file missing"}), 500

    query = request.args.get("query", "").strip().lower()
    
    # Read binary bytes of pcap and find readable strings
    with open(filepath, "rb") as f:
        data = f.read()

    # Extract printable string chunks from pcap
    printable_chunks = []
    current = bytearray()
    for b in data:
        if 32 <= b <= 126 or b in (9, 10, 13):
            current.append(b)
        else:
            if len(current) >= 4:
                printable_chunks.append(current.decode('ascii', errors='ignore'))
            current = bytearray()
    if len(current) >= 4:
        printable_chunks.append(current.decode('ascii', errors='ignore'))

    filtered = [chunk for chunk in printable_chunks if not query or query in chunk.lower()]
    return jsonify({"results": filtered})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
