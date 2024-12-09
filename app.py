from flask import Flask, render_template, request, redirect, url_for,g
import sqlite3

app= Flask(__name__)
conn = sqlite3.connect('project.db')
cursor = conn.cursor()

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
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/superadmin")
def superadmin():
    return render_template("sa_homepage.html")

@app.route("/usersignup")
def usersignup():
    return render_template("u_signup.html")

@app.route("/caresignup")
def caresignup():
    return render_template("c_signup.html")

if __name__ == "__main__":
    app.run(debug=True)
