import os
import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)
DB_PATH = '/tmp/challenge.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS patients")
    cursor.execute("DROP TABLE IF EXISTS secrets")
    
    # Customized schema
    cursor.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, diagnosis TEXT NOT NULL)")
    cursor.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY AUTOINCREMENT, flag TEXT NOT NULL)")
    
    # Customized data
    patients = [
        ("John Doe", "Flu"),
        ("Jane Smith", "Broken Arm"),
        ("Alice Johnson", "Migraine"),
        ("Bob Brown", "Sprained Ankle")
    ]
    cursor.executemany("INSERT INTO patients (name, diagnosis) VALUES (?, ?)", patients)
    
    # FLAG integration remains standard
    flag = os.environ.get("FLAG", "flag{test_hospital_sqli}")
    cursor.execute("INSERT INTO secrets (flag) VALUES (?)", (flag,))
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    query = ""
    results = []
    error = ""
    
    if request.method == "POST":
        query = request.form.get("patient_name", "")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vulnerability remains
        sql_query = f"SELECT name, diagnosis FROM patients WHERE name LIKE '%{query}%'"
        
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
