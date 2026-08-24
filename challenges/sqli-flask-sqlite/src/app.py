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
    cursor.execute("CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL)")
    cursor.execute("CREATE TABLE flag_store (id INTEGER PRIMARY KEY AUTOINCREMENT, flag TEXT NOT NULL)")
    
    products = [
        ("Quantum Analyzer", "Examine quantum states."),
        ("Aether Engine", "Clean renewable engine."),
        ("Chrono Pocket Watch", "Perceive time slower."),
        ("Cyber Deck v9", "Neural link terminal."),
        ("Nanite Repair Kit", "Repairs micro-fractures.")
    ]
    cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", products)
    
    flag = os.environ.get("FLAG", "flag{s1mpl3_sqli_f0r_b3g1nn3rs_9a12c8}")
    cursor.execute("INSERT INTO flag_store (flag) VALUES (?)", (flag,))
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    error = ""
    
    if request.method == "POST":
        query = request.form.get("query", "")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # VULNERABLE QUERY
        sql_query = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
        
        try:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        except sqlite3.Error as e:
            error = str(e)
        finally:
            conn.close()
            
    return render_template("index.html", query=query, results=results, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
