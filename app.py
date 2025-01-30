import os
from flask import Flask, flash, render_template, request, redirect, url_for,g, session
import sqlite3
from werkzeug.utils import secure_filename

app= Flask(__name__)
app.secret_key = 'Nareen_is_very_handsome'
conn = sqlite3.connect('project.db')
cursor = conn.cursor()

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#this method creates the tables in the database
def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age TEXT NOT NULL,
            gender TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            ph_num TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caretaker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age TEXT NOT NULL,
            gender TEXT NOT NULL,
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
        g.db.row_factory = sqlite3.Row
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

###############################################LOGIN####################################################
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
                cursor.execute('SELECT id FROM caretaker WHERE username = ? AND password = ?', (username, password))
                user_id= cursor.fetchone()[0]
                session['user_id'] = user_id  # Store user_id in session
                return redirect(url_for('caretaker'))
        
            cursor.execute('SELECT * FROM user WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                cursor.execute('SELECT id FROM user WHERE username = ? AND password = ?', (username, password))
                user_id= cursor.fetchone()[0]
                session['user_id'] = user_id  # Store user_id in session
                return redirect(url_for('user'))
            
            cursor.execute('SELECT * FROM admin WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                cursor.execute('SELECT id FROM admin WHERE username = ? AND password = ?', (username, password))
                user_id= cursor.fetchone()[0]
                session['user_id'] = user_id # Store user_id in session
                return redirect(url_for('admin'))
            
            cursor.execute('SELECT * FROM super_admin WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                cursor.execute('SELECT id FROM super_admin WHERE username = ? AND password = ?', (username, password))
                user_id= cursor.fetchone()[0]
                session['user_id'] = user_id  # Store user_id in session
                return redirect(url_for('superadmin'))
            else:
                flash("Invalid username or password")
            
        except Exception as e:
            return ("An error occured: " + str(e))
        
    return render_template("login.html")

###############################################SIGNUP####################################################
#this is the signup route and method
@app.route("/signup")
def signup():
    return render_template("signup.html")
###############################################SUPER ADMIN####################################################
#this is the superadmin login route and method
@app.route("/superadmin")
def superadmin():
    return render_template("SuperAdmin/superadmin.html")

###############################################ADMIN####################################################
#this is the admin login route and method
@app.route("/admin")
def admin():
    return render_template("Admin/adminhomepage.html")

###############################################USER####################################################
#this is the user login route and method
@app.route("/user")
def user():
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    
    with open("static/img_log/user/"+ str_user_id + ".txt", "a+") as file:
        file.seek(0)
        image_name = str(file.read())
        if image_name:
            image_url= url_for('static', filename='uploads/'+ image_name )
        else:
            image_name = "user.jpg"
            image_url= url_for('static', filename='uploads/'+ image_name )
            file.write(image_name)  # Store the value
                
    return render_template("User/userhomepage.html", image_url=image_url, image_name=image_name)

@app.route("/usersignup", methods=["GET", "POST"])
def usersignup():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        name=  request.form["name"]
        age=  request.form["age"]
        gender=  request.form["gender"]
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
            cursor.execute('INSERT INTO user (name, age, gender, username, password, ph_num) VALUES (?, ?, ?, ?, ?, ?)', (name, age, gender, username, password, phone))
            db.commit()
            flash("Account created successfully")
            return redirect("/login")
            
        except Exception as e:
            return ("An error occured: " + str(e))
            
        finally:
            db.close()
    return render_template("User/u_signup.html")

@app.route("/userprofile", methods=["GET", "POST"])
def userprofile():
    db = get_db()
    cursor = db.cursor()
    
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    if not user_id:
        return redirect(url_for('login'))
    
    cursor.execute('SELECT * FROM user WHERE id = ?',(user_id,))
    user = cursor.fetchone()
    db.close()
    
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("User/u_profile.html", user=user, image_url=image_url, image_name=image_name)

@app.route("/edituser", methods=["GET", "POST"])
def edituser():
    if request.method == 'POST':
        # Check if the form contains a file
        if 'image' not in request.files:
            return 'No file part'
        
        file = request.files['image']
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            # Secure the filename (to prevent directory traversal attacks)
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Check if there is an existing image, and remove it if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Save the new file
            file.save(file_path)
            image_name=filename
           
            user_id = session.get('user_id')
            str_user_id = str(user_id)
            
            with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
                x = str(file.read())
                if x == image_name:
                    return userprofile()
                else:
                    with open("static/img_log/user/"+ str_user_id + ".txt", "w") as file:
                        file.write(image_name)  # Store the value
                    return userprofile()
        
        #Enter the saved data into the database
        db = get_db()
        cursor = db.cursor()
        
        user_id = session.get('user_id')
        
        if request.method == "POST":
            name = request.form["name"].strip()
            age = request.form["age"].strip()
            gender = request.form["gender"].strip()
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            contact = request.form["contact"].strip()
            
            update_fields = {}
            if name:
                update_fields["name"] = name
            if age:
                update_fields["age"] = age
            if gender:
                update_fields["gender"] = gender
            if username:
                update_fields["username"] = username
            if password:
                update_fields["password"] = password
            if contact:
                update_fields["ph_num"] = contact
            
            if update_fields:  # Update only if there are changes
                update_query = "UPDATE user SET " + ", ".join(f"{key} = ?" for key in update_fields.keys()) + " WHERE id = ?"
                db.execute(update_query, tuple(update_fields.values()) + (user_id,))
                db.commit()
                db.close()
            
            return redirect(url_for("userprofile"))
    
    return redirect("/userprofile")  # Render the profile page

@app.route("/removeuser", methods=["GET", "POST"])
def removeuser():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get('user_id')

    cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('signup'))

###############################################CARETAKER####################################################
#this is the caretaker login route and method
@app.route("/caretaker")
def caretaker():
    return render_template("Caretaker/caretakerhomepage.html")

@app.route("/caresignup", methods= ["GET", "POST"])
def caresignup():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        name=  request.form["name"]
        age=  request.form["age"]
        gender=  request.form["gender"]
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
            cursor.execute('INSERT INTO caretaker (name, age, gender, username, password, ph_num) VALUES (?, ?, ?, ?, ?, ?)', (name, age, gender, username, password, phone))
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
