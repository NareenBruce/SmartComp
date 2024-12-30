from flask import Flask, flash, render_template, request, redirect, url_for,g
import sqlite3

app= Flask(__name__)
app.secret_key = 'Nareen_is_very_handsome'
conn = sqlite3.connect('project.db')
cursor = conn.cursor()

#this method creates the tables in the database
def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            ph_num TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caretaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            ph_num TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS super_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
#this method connects to the database
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('project.db')
    return g.db

#this method closes the database connection
@app.teardown_appcontext
def close_db(exception):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        
#this is the homepage route and method
@app.route("/")
def home():
    return render_template("main.html")

#this is the login route and method
@app.route("/login", methods=["GET", "POST"])
def login():
    db= get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        try:
            cursor.execute('SELECT * FROM caretaker WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                return render_template("Caretaker/caretakerhomepage.html")
        
            cursor.execute('SELECT * FROM user WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                return render_template("User/userhomepage.html")
            else:
                flash("Invalid username or password")
            
        except Exception as e:
            return ("An error occured: " + str(e))
        
    return render_template("login.html")

#this is the signup route and method
@app.route("/signup")
def signup():
    return render_template("signup.html")

#this is the superadmin login route and method
@app.route("/superadmin")
def superadmin():
    return render_template("SuperAdmin/superadminlogin.html")

#this is the user login route and method
@app.route("/usersignup", methods=["GET", "POST"])
def usersignup():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        name=  request.form["name"]
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
            cursor.execute('INSERT INTO user (name, username, password, ph_num) VALUES (?, ?, ?, ?)', (name, username, password, phone))
            db.commit()
            flash("Account created successfully")
            return redirect("/login")
            
        except Exception as e:
            return ("An error occured: " + str(e))
            
        finally:
            db.close()
    return render_template("User/u_signup.html")

#this is the caretaker login route and method
@app.route("/caresignup", methods= ["GET", "POST"])
def caresignup():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        name=  request.form["name"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone = request.form["phone"]
    
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect("/caresignup")
        try: 
            #check if already exists
            cursor.execute('SELECT * FROM caretaker WHERE username=? AND password=?', (username,password))
            existing_acc= cursor.fetchone()
            if existing_acc is not None:
                flash ("User already exists")
                return redirect("/caresignup")
            
            #add the user to database
            cursor.execute('INSERT INTO caretaker (name, username, password, ph_num) VALUES (?, ?, ?, ?)', (name, username, password, phone))
            db.commit()
            flash("Account created successfully")
            return redirect("/login")
            
        except Exception as e:
            return ("An error occured: " + str(e))
            
        finally:
            db.close()
    return render_template("Caretaker/c_signup.html")

#this is the part of code that runs the app
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
