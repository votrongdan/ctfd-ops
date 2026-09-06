import os
import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)
DB_PATH = '/tmp/challenge.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS flag_store")
    
    # CAREFUL: Changing table names or schemas here means you must update your solve scripts
    # and intended payloads.
    cursor.execute("CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL)")
    cursor.execute("CREATE TABLE flag_store (id INTEGER PRIMARY KEY AUTOINCREMENT, flag TEXT NOT NULL)")
    
    # SAFE TO CUSTOMIZE: You can change the sample data to fit your challenge's story.
    products = [
        ("Quantum Analyzer", "Examine quantum states."),
        ("Aether Engine", "Clean renewable engine."),
        ("Chrono Pocket Watch", "Perceive time slower."),
        ("Cyber Deck v9", "Neural link terminal."),
        ("Nanite Repair Kit", "Repairs micro-fractures.")
    ]
    cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", products)
    
    # FLAG: Read from environment variable injected by CTFd Whale. 
    # Do not hardcode the flag. Do not change how the environment variable is fetched unless you know what you're doing.
    flag = os.environ.get("FLAG", "flag{s1mpl3_sqli_f0r_b3g1nn3rs_9a12c8}")
    cursor.execute("INSERT INTO flag_store (flag) VALUES (?)", (flag,))
    conn.commit()
    conn.close()

init_db()

# CAREFUL: Changing the route or method will require updating your writeup and scripts.
@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    error = ""
    
    if request.method == "POST":
        query = request.form.get("query", "")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # VULNERABILITY: This is the vulnerable SQL query using string formatting.
        # If you change this to use parameterized queries (?, ?), the vulnerability will disappear.
        sql_query = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
        
        try:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        except sqlite3.Error as e:
            error = str(e)
        finally:
            conn.close()
            
    # SAFE TO CUSTOMIZE: Changing the template doesn't affect the vulnerability, 
    # as long as the form still sends a POST request with the 'query' parameter.
    return render_template("index.html", query=query, results=results, error=error)

if __name__ == "__main__":
    # RUNTIME: Must listen on 0.0.0.0 to be accessible inside the Docker container.
    app.run(host="0.0.0.0", port=80)
