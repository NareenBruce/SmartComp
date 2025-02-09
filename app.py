import os
from flask import Flask, flash, render_template, request, redirect, url_for,g, session, jsonify, Response
import sqlite3
import time
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import re 
import datetime
from string import ascii_uppercase
from werkzeug.utils import secure_filename

app= Flask(__name__)
app.secret_key = 'Nareen_is_very_handsome'
conn = sqlite3.connect('project.db')
cursor = conn.cursor()
socketio = SocketIO(app)

#this is the dictionary that stores the rooms fr chats
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

MEDICAL_REPORTS_FOLDER = "static/report/user"  # Define a unique variable name
os.makedirs(MEDICAL_REPORTS_FOLDER, exist_ok=True)  # Ensure folder exists
ALLOWED_EXTENSION = {'pdf'}  # Only allow PDF files

def allowed_files(filename):
    """Check if file has an allowed extension (PDF)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION


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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            rel_id INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            uploaded_date TEXT NOT NULL,
            pdf_name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assign (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_name TEXT NOT NULL,
           user_id TEXT NOT NULL,
           caretaker_name TEXT NOT NULL,
           caretaker_id TEXT NOT NULL
           )
    ''')
    conn.commit()
    conn.close()

def get_contact_info(contact_num):
    """Fetch user ID and name from `user` or `caretaker` table."""
    db = get_db()  # Get a new database connection for this request
    cursor = db.cursor()

    # Check in `user` table first
    cursor.execute("SELECT id, name FROM user WHERE ph_num=?", (contact_num,))
    result = cursor.fetchone()

    # If not found, check in `caretaker` table
    if not result:
        cursor.execute("SELECT id, name FROM caretaker WHERE ph_num=?", (contact_num,))
        result = cursor.fetchone()

    return result  # Returns (id, name) or None
    
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
                care_id= cursor.fetchone()[0]
                session['care_id'] = care_id  # Store user_id in session
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
                admin_id= cursor.fetchone()[0]
                session['admin_id'] = admin_id # Store user_id in session
                return redirect(url_for('admin'))
            
            cursor.execute('SELECT * FROM super_admin WHERE username = ? AND password = ?', (username, password))
            if cursor.fetchone() is not None:
                cursor.execute('SELECT id FROM super_admin WHERE username = ? AND password = ?', (username, password))
                sa_id= cursor.fetchone()[0]
                session['sa_id'] = sa_id  # Store user_id in session
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
    sa_id = session.get('sa_id')
    str_sa_id = str(sa_id)
    
    with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "a+") as file:
        file.seek(0)
        image_name = str(file.read())
        if image_name:
            image_url= url_for('static', filename='uploads/'+ image_name )
        else:
            image_name = "user.jpg"
            image_url= url_for('static', filename='uploads/'+ image_name )
            file.write(image_name)  # Store the value
                
    return render_template("SuperAdmin/su_homepage.html", image_url=image_url, image_name=image_name)

@app.route("/su_profile", methods=["GET", "POST"])
def su_profile():
    db = get_db()
    cursor = db.cursor()
    
    sa_id = session.get('sa_id')
    str_sa_id = str(sa_id)
    if not sa_id:
        return redirect(url_for('login'))
    
    cursor.execute('SELECT * FROM super_admin WHERE id = ?',(sa_id,))
    admin = cursor.fetchone()
    db.close()
    
    with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("SuperAdmin/profile.html", admin=admin, image_url=image_url, image_name=image_name)

@app.route("/editsuadmin", methods=["GET", "POST"])
def editsuadmin():
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
           
            sa_id = session.get('sa_id')
            str_sa_id = str(sa_id)
            
            with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "r") as file:
                x = str(file.read())
                if x == image_name:
                    return su_profile()
                else:
                    with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "w") as file:
                        file.write(image_name)  # Store the value
                    return su_profile()
        
        #Enter the saved data into the database
        db = get_db()
        cursor = db.cursor()
        
        sa_id = session.get('sa_id')
        
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            
            update_fields = {}
            if username:
                update_fields["username"] = username
            if password:
                update_fields["password"] = password
            
            if update_fields:  # Update only if there are changes
                update_query = "UPDATE super_admin SET " + ", ".join(f"{key} = ?" for key in update_fields.keys()) + " WHERE id = ?"
                db.execute(update_query, tuple(update_fields.values()) + (sa_id,))
                db.commit()
                db.close()
            
            return redirect(url_for("su_profile"))
    
    return redirect("/su_profile")  # Render the profile page

@app.route("/removesuadmin", methods=["GET", "POST"])
def removesuadmin():
    db = get_db()
    cursor = db.cursor()
    sa_id = session.get('sa_id')

    cursor.execute('DELETE FROM super_admin WHERE id = ?', (sa_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('signup')) 
    
@app.route("/adminmanage", methods=["GET", "POST"])
def adminmanage():
    sa_id = session.get('sa_id')
    str_sa_id = str(sa_id)
    
    db= get_db()
    cursor = db.cursor()
    
    #To display contacts
    cursor.execute("SELECT * FROM admin")
    contacts_list = cursor.fetchall()  # Fetch all matching rows
    db.close()

    with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("SuperAdmin/adminmanage.html",image_url=image_url, contacts=contacts_list)

@app.route("/deladmin", methods=["GET", "POST"])
def deladmin():
    db= get_db()
    cursor = db.cursor()
    
    admin_id= request.args.get('p_id')
    cursor.execute('DELETE FROM admin WHERE id=?', (admin_id,))
    db.commit()
    db.close()
    flash("Contact deleted successfully!")
    return redirect(url_for('adminmanage'))

@app.route("/addadmin", methods=["GET", "POST"])
def addadmin():
    db = get_db()
    cursor = db.cursor()

    admin_user = request.form["admin_user"]
    admin_pass = request.form["admin_pass"]

    # Check if admin already exists
    cursor.execute("SELECT * FROM admin WHERE username = ?", (admin_user,))
    existing_admin = cursor.fetchone()

    if existing_admin:
        flash("Admin username already exists!")
        db.close()
        return redirect(url_for("adminmanage"))

    # Insert new admin
    cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", (admin_user, admin_pass))
    db.commit()
    db.close()

    flash("New admin added successfully!")
    return redirect(url_for("adminmanage"))

@app.route("/systemsight", methods=["GET", "POST"])
def systemsight():
    db = get_db()
    cursor = db.cursor()
    
    sa_id = session.get('sa_id')
    str_sa_id = str(sa_id)
    
    # Count total users
    cursor.execute("SELECT COUNT(*) FROM user")
    user_count = cursor.fetchone()[0]

    # Count total caretakers
    cursor.execute("SELECT COUNT(*) FROM caretaker")
    caretaker_count = cursor.fetchone()[0]

    # Count total admins
    cursor.execute("SELECT COUNT(*) FROM admin")
    admin_count = cursor.fetchone()[0]
    
    with open("static/img_log/su_admin/"+ str_sa_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("SuperAdmin/systemsight.html", image_url=image_url, user_count=user_count, caretaker_count=caretaker_count, admin_count=admin_count)

###############################################ADMIN####################################################
#this is the admin login route and method
@app.route("/admin")
def admin():
    admin_id = session.get('admin_id')
    str_admin_id = str(admin_id)
    
    with open("static/img_log/admin/"+ str_admin_id + ".txt", "a+") as file:
        file.seek(0)
        image_name = str(file.read())
        if image_name:
            image_url= url_for('static', filename='uploads/'+ image_name )
        else:
            image_name = "user.jpg"
            image_url= url_for('static', filename='uploads/'+ image_name )
            file.write(image_name)  # Store the value
                
    return render_template("Admin/adminhomepage.html", image_url=image_url, image_name=image_name)

@app.route("/adminprofile", methods=["GET", "POST"])
def adminprofile():
    db = get_db()
    cursor = db.cursor()
    
    admin_id = session.get('admin_id')
    str_admin_id = str(admin_id)
    if not admin_id:
        return redirect(url_for('login'))
    
    cursor.execute('SELECT * FROM admin WHERE id = ?',(admin_id,))
    admin = cursor.fetchone()
    db.close()
    
    with open("static/img_log/admin/"+ str_admin_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Admin/profile.html", admin=admin, image_url=image_url, image_name=image_name)

@app.route("/editadmin", methods=["GET", "POST"])
def editadmin():
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
           
            admin_id = session.get('admin_id')
            str_admin_id = str(admin_id)
            
            with open("static/img_log/admin/"+ str_admin_id + ".txt", "r") as file:
                x = str(file.read())
                if x == image_name:
                    return adminprofile()
                else:
                    with open("static/img_log/admin/"+ str_admin_id + ".txt", "w") as file:
                        file.write(image_name)  # Store the value
                    return adminprofile()
        
        #Enter the saved data into the database
        db = get_db()
        cursor = db.cursor()
        
        admin_id = session.get('admin_id')
        
        if request.method == "POST":
            username = request.form["username"].strip()
            password = request.form["password"].strip()
            
            update_fields = {}
            if username:
                update_fields["username"] = username
            if password:
                update_fields["password"] = password
            
            if update_fields:  # Update only if there are changes
                update_query = "UPDATE admin SET " + ", ".join(f"{key} = ?" for key in update_fields.keys()) + " WHERE id = ?"
                db.execute(update_query, tuple(update_fields.values()) + (admin_id,))
                db.commit()
                db.close()
            
            return redirect(url_for("adminprofile"))
    
    return redirect("/adminprofile")  # Render the profile page

@app.route("/removeadmin", methods=["GET", "POST"])
def removeadmin():
    db = get_db()
    cursor = db.cursor()
    admin_id = session.get('admin_id')

    cursor.execute('DELETE FROM admin WHERE id = ?', (admin_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('signup')) 

@app.route("/aviewusers", methods=["GET", "POST"])
def aviewusers():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    admin_id = session.get('admin_id')
    str_admin_id = str(admin_id)
    with open("static/img_log/admin/"+ str_admin_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM user ")
    patient_list = cursor.fetchall()  # Fetch all matching rows
    db.close()
    return render_template("admin/viewuser.html", image_url=image_url, contacts=patient_list)

@app.route("/aviewuserprofile", methods=["GET", "POST"])
def aviewfuserprofile():
    db = get_db()
    cursor = db.cursor()
    
    user_id = request.args.get('p_id')
    #Fetch data for user information
    cursor.execute('SELECT * FROM user WHERE id = ?',(user_id,))
    user = cursor.fetchone()
    str_user_id =  str(user[0])
    
    #Fetch data for Medica data report
    cursor.execute('SELECT * FROM medical_data WHERE user_id = ?',(user_id,))
    report = cursor.fetchall()
    db.close()
    
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Admin/viewuserprofile.html", user=user, image_url=image_url, image_name=image_name, report=report)

@app.route("/adeleteuser", methods=["GET", "POST"])
def adeleteuser():
    db = get_db()
    cursor = db.cursor()
    user_id = request.args.get('u_id')
    cursor.execute("SELECT ph_num FROM user WHERE id = ?", (user_id,))
    contact_number = cursor.fetchone()[0]
    cursor.execute("DELETE FROM contact WHERE contact_number = ?", (contact_number,))
    cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
    cursor.execute("DELETE FROM assign WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM medical_data WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM locations WHERE user_id = ?", (user_id,))
    
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('aviewusers')) 

@app.route("/aviewcare", methods=["GET", "POST"])
def aviewcare():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    admin_id = session.get('admin_id')
    str_admin_id = str(admin_id)
    with open("static/img_log/admin/"+ str_admin_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM caretaker ")
    patient_list = cursor.fetchall()  # Fetch all matching rows
    db.close()
    return render_template("admin/viewcare.html", image_url=image_url, contacts=patient_list)

@app.route("/aviewcareprofile", methods=["GET", "POST"])
def aviewcareprofile():
    db = get_db()
    cursor = db.cursor()
    
    user_id = request.args.get('p_id')
    #Fetch data for user information
    cursor.execute('SELECT * FROM caretaker WHERE id = ?',(user_id,))
    user = cursor.fetchone()
    str_user_id =  str(user[0])
    db.close()
    
    with open("static/img_log/caretaker/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Admin/viewcareprofile.html", user=user, image_url=image_url, image_name=image_name)

@app.route("/adeletecare", methods=["GET", "POST"])
def adeletecare():
    db = get_db()
    cursor = db.cursor()
    user_id = request.args.get('u_id')
    str_user_id = str(user_id)
    cursor.execute("SELECT ph_num FROM caretaker WHERE id = ?", (user_id,))
    contact_number = cursor.fetchone()[0]
    cursor.execute("DELETE FROM contact WHERE contact_number = ?", (contact_number,))
    cursor.execute('DELETE FROM caretaker WHERE id = ?', (str_user_id,))
    cursor.execute("DELETE FROM assign WHERE caretaker_id = ?", (str_user_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('aviewcare')) 

@app.route("/assign", methods=["GET", "POST"])
def assign():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        user_id = request.form["user_id"]
        caretaker_id = request.form["caretaker_id"]

        # Fetch user and caretaker names
        cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
        user_name = cursor.fetchone()
        
        cursor.execute("SELECT name FROM caretaker WHERE id = ?", (caretaker_id,))
        caretaker_name = cursor.fetchone()

        if not user_name or not caretaker_name:
            flash("Invalid selection, please try again.")
            return redirect(url_for("assign"))

        # Check if user is already assigned
        cursor.execute("SELECT * FROM assign WHERE user_id = ?", (user_id,))
        existing_assignment = cursor.fetchone()
        
        if existing_assignment:
            flash("This user is already assigned to a caretaker!")
            return redirect(url_for("assign"))

        # Assign caretaker to user
        cursor.execute("""
            INSERT INTO assign (user_name, user_id, caretaker_name, caretaker_id)
            VALUES (?, ?, ?, ?)
        """, (user_name[0], user_id, caretaker_name[0], caretaker_id))
        
        db.commit()
        flash("Assignment successful!")
        return redirect(url_for("assign"))

    # Fetch available users (users who are not assigned)
    cursor.execute("""
        SELECT id, name FROM user 
        WHERE id NOT IN (SELECT user_id FROM assign)
    """)
    available_users = cursor.fetchall()

    # Fetch all caretakers (caretaker can have multiple users)
    cursor.execute("""
        SELECT id, name FROM caretaker
    """)
    available_caretakers = cursor.fetchall()
    
    admin_id = session.get('admin_id')
    str_admin_id = str(admin_id)
    with open("static/img_log/admin/"+ str_admin_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
        
    # Fetch assigned users table
    cursor.execute("""
        SELECT * FROM assign
    """)
    assigned_users = cursor.fetchall()

    db.close()

    db.close()
    
    return render_template("Admin/assign.html", available_users=available_users, available_caretakers=available_caretakers, image_url=image_url, assigned_users=assigned_users)

@app.route("/unassign", methods=["POST"])
def unassign():
    user_id = request.form["user_id"]
    
    db = get_db()
    cursor = db.cursor()

    # Delete user assignment
    cursor.execute("DELETE FROM assign WHERE user_id = ?", (user_id,))
    
    db.commit()
    db.close()
    
    flash("User has been unassigned from caretaker.")
    return redirect(url_for("assign"))

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
        
        # Validate phone number (only digits allowed)
        if not re.match(r"^0\d{9}$", phone):
            flash("Invalid phone number! Must start with 0 and be 10 digits long.")
            return redirect("/usersignup")
        
        try: 
            #check if alr exists
            cursor.execute('SELECT * FROM user WHERE username=? AND password=?', (username,password))
            existing_acc= cursor.fetchone()
            if existing_acc is not None:
                flash ("User already exists")
                return redirect("/usersignup")
            
            #check if username exists
            cursor.execute('SELECT * FROM user WHERE username=?', (username,))
            existing_user= cursor.fetchone()
            if existing_user is not None:
                flash ("Username already exists")
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

    cursor.execute("SELECT ph_num FROM user WHERE id = ?", (user_id,))
    contact_number = cursor.fetchone()[0]
    cursor.execute("DELETE FROM contact WHERE contact_number = ?", (contact_number,))
    cursor.execute('DELETE FROM user WHERE id = ?', (user_id,))
    cursor.execute("DELETE FROM assign WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM medical_data WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM locations WHERE user_id = ?", (user_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('signup'))

@app.route("/contactuser")
def contactuser():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM contact where rel_id = ?", (user_id,))
    contacts_list = cursor.fetchall()  # Fetch all matching rows
    db.close()
    return render_template("User/contact.html", image_url=image_url, contacts=contacts_list)

@app.route("/addcontact", methods=["GET", "POST"])
def addcontact():
    db= get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        user_id = session.get('user_id')
        name = request.form["name"]
        contact_number = request.form["contact_number"]
        #check if the contact number exist in caretaker or user table
        cursor.execute("SELECT * FROM user WHERE ph_num=?", (contact_number,))
        user = cursor.fetchone()
        if user is None:
            cursor.execute("SELECT * FROM caretaker WHERE ph_num=?", (contact_number,))
            caretaker = cursor.fetchone()
            user = caretaker
            if caretaker is None:
                flash("Contact number does not exist")
                return redirect("/contactuser")
        
        ##check if contact already exists
        cursor.execute('SELECT * FROM contact WHERE contact_number=? AND rel_id=?', (contact_number, user_id))
        existing_contact= cursor.fetchone()
        if existing_contact is not None:
            flash ("Contact already exists")
            return redirect("/contactuser")
        else:
            cursor.execute('INSERT INTO contact (name, contact_number, rel_id) VALUES (?, ?, ?)', (name, contact_number, user_id))
            db.commit()
            db.close()
            return redirect(url_for('contactuser'))
    return redirect(url_for('contactuser'))

@app.route("/deletecontact")
def deletecontact():
    db= get_db()
    cursor = db.cursor()
    
    contact_number= request.args.get('contact_number')
    user_id = session.get('user_id')
    cursor.execute('DELETE FROM contact WHERE contact_number=? AND rel_id=?', (contact_number, user_id))
    db.commit()
    db.close()
    flash("Contact deleted successfully!")
    return redirect(url_for('contactuser'))

@app.route("/chatuser", methods=["GET", "POST"])
def chatuser():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM contact where rel_id = ?", (user_id,))
    contacts_list = cursor.fetchall()  # Fetch all matching rows
    db.commit()
    
    #For Chat
    contact_number = request.args.get('contact')
    if contact_number:
        str_contact_number = str(contact_number)
        contact_num=str_contact_number
        # Fetch the user ID and name from either `user` or `caretaker` table
        result = get_contact_info(contact_num)

        if not result:
            return "User not found", 404

        contact_id, contact_name = result  # Extract ID and Name

        # Fetch current user's name (Nareen)
        cursor.execute("SELECT name FROM user WHERE id=?", (user_id,))
        name = cursor.fetchone()
        
        if not name:
            cursor.execute("SELECT name FROM caretaker WHERE id=?", (user_id,))
            name = cursor.fetchone()
        
        name = name[0] if name else None

        # Determine user's folder (User or Caretaker)
        if name:
            user_folder = f"static/room_log/user/{user_id}/"
        else:
            user_folder = f"static/room_log/caretaker/{user_id}/"
        
        os.makedirs(user_folder, exist_ok=True)
        
        # Define recipient's folder based on their type
        cursor.execute("SELECT id FROM user WHERE id=?", (contact_id,))
        recipient_is_user = cursor.fetchone() is not None
        
        if recipient_is_user:
            contact_folder = f"static/room_log/user/{contact_id}/"
        else:
            contact_folder = f"static/room_log/caretaker/{contact_id}/"
        
        os.makedirs(contact_folder, exist_ok=True)
        
        # Define recipient's room file path (using contact's name)
        room_file_path = os.path.join(user_folder, f"{contact_name}.txt")
        contact_room_file = os.path.join(contact_folder, f"{name}.txt")
        
        room_number = None  # Initialize room_number variable
        
        # Check if a chat room file exists for this contact
        if os.path.exists(room_file_path):
            with open(room_file_path, "r") as file:
                lines = file.readlines()
            
            for line in lines:
                user_id_in_file, saved_room = line.strip().split(":")
                if user_id_in_file == str(user_id):  # Found an existing room
                    room_number = saved_room
                    break

        # If no room exists, generate a new one
        if not room_number:
            room_number = generate_unique_code(4)

            # Store the chat room in both users' folders
            with open(room_file_path, "w") as file:
                file.write(f"{user_id}:{room_number}\n")   # Store current user's ID & room number
                file.write(f"{contact_id}:{room_number}\n")  # Store Contact's ID & room number
            
            with open(contact_room_file, "w") as file:
                file.write(f"{contact_id}:{room_number}\n")   # Store Contact's ID & room number
                file.write(f"{user_id}:{room_number}\n")   # Store current user's ID & room number

        # Ensure room exists in the `rooms` dictionary
        if room_number not in rooms:
            rooms[room_number] = {"members": 0, "messages": []}

        db.commit()

        # Store room info in session
        session["room"] = room_number
        session["name"] = name

        return render_template("User/room.html", contact_number=contact_number, contact_name=contact_name)

    return render_template("User/chat.html", image_url=image_url, contacts=contacts_list)

@socketio.on("message")
def message(data):
    room = session.get("room")
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    
    join_room(room)
    send({"name": name, "message": "has entered the chat"}, to=room)
    print(f"{name} joined room {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")

    send({"name": name, "message": "has left the chat"}, to=room)
    print(f"{name} has left the room {room}")

@app.route("/locationuser")
def locationuser():
    #To display image
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    return render_template("User/location.html", image_url=image_url)

@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    user_id = session.get('user_id')
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timestamp = int(time.time())
    newtime= datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    

    if user_id and latitude and longitude:
        db = get_db()
        cursor = db.cursor()
        #get user name
        cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
        name= cursor.fetchone()[0]
        cursor.execute("INSERT INTO locations (user_id, name, latitude, longitude, timestamp) VALUES (?, ?, ?, ?, ?)", (user_id, name, latitude, longitude, newtime))
        db.commit()
        return jsonify({"message": "Location updated successfully!"}), 200
        
    else:
        flash("Location share failed")
        return jsonify({"error": "Invalid data"}), 400

@app.route("/emergencyuser")
def emergencyuser():
    db= get_db()
    cursor = db.cursor()
    user_id = session.get('user_id')
    
     #To display image
    user_id = session.get('user_id')
    str_user_id = str(user_id)
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    cursor.execute("SELECT caretaker_id FROM assign where user_id = ?", (user_id,))
    caretaker_id = cursor.fetchone()[0]
    cursor.execute("SELECT ph_num FROM caretaker where id = ?", (caretaker_id,))
    contacts = cursor.fetchone()[0]
    
    return render_template("User/emergency.html", image_url=image_url, contacts=contacts)

@app.route("/medicaluser")
def medicaluser():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get('user_id')

    #To display image
    str_user_id = str(user_id)
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display medical reports
    cursor.execute("SELECT * FROM medical_data WHERE user_id = ?", (str_user_id,))
    medical_data = cursor.fetchall()
    return render_template("User/medicaldata.html", image_url=image_url, medical_data=medical_data)

@app.route("/uploadmedical", methods=["GET", "POST"])
def uploadmedical():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        
        user_id = session.get('user_id')
        if "medical_report" not in request.files:
            flash("No file selected!")
            return redirect(request.url)

        file = request.files["medical_report"]

        if file.filename == "":
            flash("No file selected!")
            return redirect(request.url)
        
        #Get user's name fro the database
        cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
        name = cursor.fetchone()[0]
        
        str_user_id = str(user_id)
        if file and allowed_files(file.filename):
            timestamp = int(time.time())
            filename = f"{name}_{user_id}_MedicalReport_{timestamp}.pdf"  # Rename to avoid conflicts
            file_path = os.path.join(MEDICAL_REPORTS_FOLDER, filename)
            file.save(file_path)  # Save file to folder

            # Store details in database
            cursor.execute("SELECT name FROM user WHERE id=?", (str_user_id,))
            name= cursor.fetchone()[0]
            cursor.execute("""
                INSERT INTO medical_data (name, user_id, uploaded_date, pdf_name) VALUES (?, ?, DATE('now'), ?)
            """, (name, user_id, filename))
            db.commit()
            flash("Medical report uploaded successfully!")
            return medicaluser()

    return medicaluser()

@app.route("/deletemedical")
def deletemedical():
    db= get_db()
    cursor = db.cursor()
    
    report= request.args.get('report')
    user_id = session.get('user_id')
    cursor.execute('DELETE FROM medical_data WHERE pdf_name=? AND user_id=?', (report, user_id))
    db.commit()
    db.close()
    flash("Report deleted successfully!")
    return redirect(url_for('medicaluser'))

###############################################CARETAKER####################################################
#this is the caretaker login route and method
@app.route("/caretaker")
def caretaker():
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "a+") as file:
        file.seek(0)
        image_name = str(file.read())
        if image_name:
            image_url= url_for('static', filename='uploads/'+ image_name )
        else:
            image_name = "user.jpg"
            image_url= url_for('static', filename='uploads/'+ image_name )
            file.write(image_name)  # Store the value
                
    return render_template("Caretaker/caretakerhomepage.html", image_url=image_url, image_name=image_name)

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
        # Validate phone number (only digits allowed)
        if not re.match(r"^0\d{9}$", phone):
            flash("Invalid phone number! Must start with 0 and be 10 digits long.")
            return redirect("/usersignup")
        
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

@app.route("/careprofile",  methods=["GET", "POST"])
def careprofile():
    db = get_db()
    cursor = db.cursor()
    
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    if not care_id:
        return redirect(url_for('login'))
    
    cursor.execute('SELECT * FROM caretaker WHERE id = ?',(care_id,))
    caretaker = cursor.fetchone()
    db.close()
    
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Caretaker/c_profile.html", caretaker=caretaker, image_url=image_url, image_name=image_name)

@app.route("/editcare", methods=["GET", "POST"])
def editcare():
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
           
            care_id = session.get('care_id')
            str_care_id = str(care_id)
            
            with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
                x = str(file.read())
                if x == image_name:
                    return careprofile()
                else:
                    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "w") as file:
                        file.write(image_name)  # Store the value
                    return careprofile()
        
        #Enter the saved data into the database
        db = get_db()
        cursor = db.cursor()
        
        care_id = session.get('care_id')
        
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
                update_query = "UPDATE caretaker SET " + ", ".join(f"{key} = ?" for key in update_fields.keys()) + " WHERE id = ?"
                db.execute(update_query, tuple(update_fields.values()) + (care_id,))
                db.commit()
                db.close()
            
            return redirect(url_for("careprofile"))
    
    return redirect("/careprofile")  # Render the profile page

@app.route("/removecare", methods=["GET", "POST"])
def removecare():
    db = get_db()
    cursor = db.cursor()
    care_id = session.get('care_id')
    
    cursor.execute("SELECT ph_num FROM caretaker WHERE id = ?", (care_id,))
    contact_number = cursor.fetchone()[0]
    cursor.execute("DELETE FROM contact WHERE contact_number = ?", (contact_number,))
    cursor.execute('DELETE FROM caretaker WHERE id = ?', (care_id,))
    cursor.execute("DELETE FROM assign WHERE caretaker_id = ?", (care_id,))
    db.commit()
    db.close()
    flash("Account deleted successfully", "success")
    return redirect(url_for('signup'))

@app.route("/contactcare", methods=["GET", "POST"])
def contactcare():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM contact where rel_id = ?", (care_id,))
    contacts_list = cursor.fetchall()  # Fetch all matching rows
    db.close()
    return render_template("Caretaker/contact.html", image_url=image_url, contacts=contacts_list)

@app.route("/addcontactcare", methods=["GET", "POST"])
def addcontactcare():
    db= get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        care_id = session.get('care_id')
        name = request.form["name"]
        contact_number = request.form["contact_number"]
        #check if the contact number exist in caretaker or user table
        cursor.execute("SELECT * FROM user WHERE ph_num=?", (contact_number,))
        user = cursor.fetchone()
        if user is None:
            cursor.execute("SELECT * FROM caretaker WHERE ph_num=?", (contact_number,))
            caretaker = cursor.fetchone()
            user = caretaker
            if caretaker is None:
                flash("Contact number does not exist")
                return redirect("/contactcare")
        
        ##check if contact already exists
        cursor.execute('SELECT * FROM contact WHERE contact_number=? AND rel_id=?', (contact_number, care_id))
        existing_contact= cursor.fetchone()
        if existing_contact is not None:
            flash ("Contact already exists")
            return redirect("/contactcare")
        else:
            cursor.execute('INSERT INTO contact (name, contact_number, rel_id) VALUES (?, ?, ?)', (name, contact_number, care_id))
            db.commit()
            db.close()
            return redirect(url_for('contactcare'))
    return redirect(url_for('contactcare'))

@app.route("/deletecontactcare")
def deletecontactcare():
    db= get_db()
    cursor = db.cursor()
    
    contact_number= request.args.get('contact_number')
    care_id = session.get('care_id')
    cursor.execute('DELETE FROM contact WHERE contact_number=? AND rel_id=?', (contact_number, care_id))
    db.commit()
    db.close()
    flash("Contact deleted successfully!")
    return redirect(url_for('contactcare'))
    
@app.route("/chatcare", methods=["GET", "POST"])
def chatcare():
    db= get_db()
    cursor = db.cursor()
    
    #To display image
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    #To display contacts
    cursor.execute("SELECT * FROM contact where rel_id = ?", (care_id,))
    contacts_list = cursor.fetchall()  # Fetch all matching rows
    db.commit()
    
    #For Chat
    contact_number = request.args.get('contact')
    if contact_number:
        str_contact_number = str(contact_number)
        contact_num=str_contact_number
        # Fetch the user ID and name from either `user` or `caretaker` table
        result = get_contact_info(contact_num)

        if not result:
            return "User not found", 404

        contact_id, contact_name = result  # Extract ID and Name

        # Fetch current user's name (Nareen)
        cursor.execute("SELECT name FROM caretaker WHERE id=?", (care_id,))
        name = cursor.fetchone()
        
        if not name:
            cursor.execute("SELECT name FROM user WHERE id=?", (care_id,))
            name = cursor.fetchone()
        
        name = name[0] if name else None

        # Determine user's folder (User or Caretaker)
        if name:
            user_folder = f"static/room_log/caretaker/{care_id}/"
        else:
            user_folder = f"static/room_log/user/{care_id}/"
        
        os.makedirs(user_folder, exist_ok=True)
        
        # Define recipient's folder based on their type
        cursor.execute("SELECT id FROM user WHERE id=?", (contact_id,))
        recipient_is_user = cursor.fetchone() is not None
        
        if recipient_is_user:
            contact_folder = f"static/room_log/user/{contact_id}/"
        else:
            contact_folder = f"static/room_log/caretaker/{contact_id}/"
        
        os.makedirs(contact_folder, exist_ok=True)
        
        # Define recipient's room file path (using contact's name)
        room_file_path = os.path.join(user_folder, f"{contact_name}.txt")
        contact_room_file = os.path.join(contact_folder, f"{name}.txt")
        
        room_number = None  # Initialize room_number variable
        
        # Check if a chat room file exists for this contact
        if os.path.exists(room_file_path):
            with open(room_file_path, "r") as file:
                lines = file.readlines()
            
            for line in lines:
                user_id_in_file, saved_room = line.strip().split(":")
                if user_id_in_file == str(care_id):  # Found an existing room
                    room_number = saved_room
                    break

        # If no room exists, generate a new one
        if not room_number:
            room_number = generate_unique_code(4)

            # Store the chat room in both users' folders
            with open(room_file_path, "w") as file:
                file.write(f"{care_id}:{room_number}\n")   # Store current user's ID & room number
                file.write(f"{contact_id}:{room_number}\n")  # Store Contact's ID & room number
            
            with open(contact_room_file, "w") as file:
                file.write(f"{contact_id}:{room_number}\n")   # Store Contact's ID & room number
                file.write(f"{care_id}:{room_number}\n")   # Store current user's ID & room number

        # Ensure room exists in the `rooms` dictionary
        if room_number not in rooms:
            rooms[room_number] = {"members": 0, "messages": []}

        db.commit()

        # Store room info in session
        session["room"] = room_number
        session["name"] = name

        return render_template("Caretaker/room.html", contact_number=contact_number, contact_name=contact_name)

    return render_template("Caretaker/chat.html", image_url=image_url, contacts=contacts_list)

@app.route("/locationcare", methods=["GET", "POST"])
def locationcare():
    db = get_db()
    cursor = db.cursor()
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    
    cursor.execute("SELECT user_id FROM assign WHERE caretaker_id = ?", (str_care_id,))
    user_ids = cursor.fetchall() 
    location_list = []
    if not user_ids:
        flash("No users assigned to this caretaker.")
        db.close()
        return redirect(url_for("caretaker_dashboard"))
    
    for user in user_ids:
        user_id = user[0]  # Extract user_id from tuple
        cursor.execute("SELECT * FROM locations WHERE user_id = ?", (user_id,))
        location_list.extend(cursor.fetchall())  # Append all location rows
    
    db.close()
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Caretaker/location.html", image_url=image_url, contacts=location_list)

@app.route("/deletelocationcare")
def deletelocationcare():
    db= get_db()
    cursor = db.cursor()
    
    timestamp= request.args.get('time_number')
    str_timestamp = str(timestamp)
    cursor.execute('DELETE FROM locations WHERE timestamp=?', (str_timestamp,))
    db.commit()
    db.close()
    flash("Location deleted successfully!")
    return redirect(url_for('locationcare'))

@app.route("/patientscare", methods=["GET", "POST"])
def patientscare():
    db= get_db()
    cursor = db.cursor()
    
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    
    cursor.execute("SELECT user_id FROM assign WHERE caretaker_id = ?", (str_care_id,))
    user_ids = cursor.fetchall() 
    patient_list = []
    if not user_ids:
        flash("No users assigned to this caretaker.")
        db.close()
        return redirect(url_for("caretaker_dashboard"))
    
    for user in user_ids:
        user_id = user[0]  # Extract user_id from tuple
        cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,))
        patient_list.extend(cursor.fetchall())  # Append all location rows
    
    #To display image
    care_id = session.get('care_id')
    str_care_id = str(care_id)
    with open("static/img_log/caretaker/"+ str_care_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name)
    
    db.close()
    return render_template("Caretaker/patients.html", image_url=image_url, contacts=patient_list)

@app.route("/patientprofile", methods=["GET", "POST"])
def patientprofile():
    db = get_db()
    cursor = db.cursor()
    
    user_id = request.args.get('p_id')
    #Fetch data for user information
    cursor.execute('SELECT * FROM user WHERE id = ?',(user_id,))
    user = cursor.fetchone()
    str_user_id =  str(user[0])
    
    #Fetch data for Medica data report
    cursor.execute('SELECT * FROM medical_data WHERE user_id = ?',(user_id,))
    report = cursor.fetchall()
    db.close()
    
    with open("static/img_log/user/"+ str_user_id + ".txt", "r") as file:
        image_name = str(file.read())
        image_url= url_for('static', filename='uploads/'+ image_name )
    return render_template("Caretaker/patientdetails.html", user=user, image_url=image_url, image_name=image_name, report=report)

###################################################LOGOUT####################################################
@app.route("/logout")
def logout():
    session.clear()  # Clear session data
    flash("You have been logged out.")

    # Strongest Cache-Control Headers
    response = redirect(url_for("login"))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private, no-transform'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Set-Cookie'] = 'session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; HttpOnly; Secure; SameSite=Lax'

    return response


#this is the part of code that runs the app
if __name__ == "__main__":
    create_table()
    app.run(debug=True)