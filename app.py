from flask import Flask, flash, render_template, request, redirect, url_for,g
import sqlite3

app= Flask(__name__)
app.secret_key = 'Nareen_is_very_handsome'
conn = sqlite3.connect('project.db')
cursor = conn.cursor()

def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            ph_num TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caretaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            ph_num TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('project.db')
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Close the database connection at the end of the request."""
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

@app.route("/usersignup", methods=["GET", "POST"])
def usersignup():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone = request.form["phone"]
    
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect("/usersignup")
        try: 
            #check if alr exists
            cursor.execute('SELECT * FROM user WHERE username=? AND password=?', (username,password))
            existing_acc= cursor.fetchone()
            if existing_acc is not None:
                flash ("User already exists")
                return redirect("/usersignup")
            
            #add the user to database
            cursor.execute('INSERT INTO user (username, password, ph_num) VALUES (?, ?, ?)', (username, password, phone))
            db.commit()
            return ("You have successfully signed up!")
            
        except Exception as e:
            return ("An error occured: " + str(e))
            
        finally:
            db.close()
    return render_template("u_signup.html")

@app.route("/caresignup")
def caresignup():
    return render_template("c_signup.html")

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
