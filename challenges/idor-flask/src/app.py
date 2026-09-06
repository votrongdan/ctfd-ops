import os
import sqlite3
from flask import Flask, request, render_template, abort

app = Flask(__name__)
DB_PATH = '/tmp/challenge.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS notes")
    cursor.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT, content TEXT)")
    
    # Admin note (user_id = 1)
    flag = os.environ.get("FLAG", "flag{idor_test_flag_999}")
    cursor.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (1, "Secret Admin Note", flag))
    
    # Other user notes
    cursor.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (2, "Shopping List", "Milk, Eggs, Bread"))
    cursor.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (3, "Todo", "Finish the CTF challenge"))
    
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    # Simulate a logged-in user with user_id = 2
    # In a real app, this would come from a session cookie
    current_user_id = 2
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM notes WHERE user_id = ?", (current_user_id,))
    notes = cursor.fetchall()
    conn.close()
    
    return render_template("index.html", notes=notes)

@app.route("/note")
def view_note():
    note_id = request.args.get("id")
    if not note_id:
        return "Missing note id", 400
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()
    conn.close()
    
    if not note:
        return "Note not found", 404
        
    # VULNERABILITY: Missing authorization check. 
    # The application does not check if the note belongs to the current_user_id.
    # Anyone can read any note by changing the 'id' parameter.
    
    return render_template("note.html", title=note[0], content=note[1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
