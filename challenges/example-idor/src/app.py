import os
import sqlite3
from flask import Flask, request, render_template

app = Flask(__name__)
DB_PATH = '/tmp/bank.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute("CREATE TABLE accounts (acc_num INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, balance TEXT, secret_info TEXT)")
    
    # VIP Account (owner_id = 999)
    flag = os.environ.get("FLAG", "flag{test_bank_idor}")
    # Setting VIP account number to 100
    cursor.execute("INSERT INTO accounts (acc_num, owner_id, balance, secret_info) VALUES (?, ?, ?, ?)", (100, 999, "$10,000,000", flag))
    
    # Regular users
    cursor.execute("INSERT INTO accounts (acc_num, owner_id, balance, secret_info) VALUES (?, ?, ?, ?)", (101, 10, "$150", "N/A"))
    cursor.execute("INSERT INTO accounts (acc_num, owner_id, balance, secret_info) VALUES (?, ?, ?, ?)", (102, 11, "$2,000", "Saving for a car"))
    
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    # Logged in as user 10
    current_user_id = 10
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT acc_num, balance FROM accounts WHERE owner_id = ?", (current_user_id,))
    accounts = cursor.fetchall()
    conn.close()
    
    return render_template("index.html", accounts=accounts)

@app.route("/account")
def view_account():
    acc_num = request.args.get("no")
    if not acc_num:
        return "Missing account number", 400
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, secret_info FROM accounts WHERE acc_num = ?", (acc_num,))
    account = cursor.fetchone()
    conn.close()
    
    if not account:
        return "Account not found", 404
        
    return render_template("account.html", balance=account[0], secret=account[1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
