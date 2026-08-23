import os
import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)

DB_PATH = '/tmp/challenge.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Reset database tables
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS flag_store")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE flag_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flag TEXT NOT NULL
        )
    """)
    
    # Populate products
    products = [
        ("Quantum Analyzer", "Examine quantum states with extreme precision."),
        ("Aether Engine", "Clean renewable engine powered by background cosmic radiation."),
        ("Chrono Pocket Watch", "Allows wearer to perceive local time 5% slower."),
        ("Cyber Deck v9", "Pre-configured neural link terminal for netrunning."),
        ("Nanite Repair Kit", "Repairs structural micro-fractures in high-tech alloys.")
    ]
    cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?)", products)
    
    # Insert the dynamic flag from the environment variable (or a default for testing)
    flag = os.environ.get("FLAG", "flag{s1mpl3_sqli_f0r_b3g1nn3rs_9a12c8}")
    cursor.execute("INSERT INTO flag_store (flag) VALUES (?)", (flag,))
    
    conn.commit()
    conn.close()

# Initialize DB on app import
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
        
        # VULNERABLE QUERY: String formatting inside SQL
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
    # Fallback to port 80 if executed directly
    app.run(host="0.0.0.0", port=80)
