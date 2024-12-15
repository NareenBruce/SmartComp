from flask import Flask, render_template, request, redirect, url_for,g
import sqlite3

app= Flask(__name__)
conn = sqlite3.connect('project.db')
cursor = conn.cursor()

def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('project.db')
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/login")
def login(username, password):
    return render_template("login.html")

def loginauth(username, password):
    cursor.execute('SELECT * FROM login WHERE username = ? AND password = ?', (username, password))
    if cursor.fetchone() is not None:
        return render_template("homepage.html")
    else:
        "Invalid username or password"

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/superadmin")
def superadmin():
    return render_template("sa_homepage.html")

@app.route("/usersignup")
def usersignup(username, password):
    cursor.execute('INSERT INTO login (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()
    return render_template("u_signup.html")

@app.route("/caresignup")
def caresignup():
    return render_template("c_signup.html")

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
