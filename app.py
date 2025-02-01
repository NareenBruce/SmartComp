import os
from flask import Flask, flash, render_template, request, redirect, url_for,g, session
import sqlite3
from flask_socketio import join_room, leave_room, send, SocketIO
import random
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
    conn.commit()
    conn.close()

def get_contact_info(contact_name):
    """Fetch user ID and name from `user` or `caretaker` table."""
    db = get_db()  # Get a new database connection for this request
    cursor = db.cursor()

    # Check in `user` table first
    cursor.execute("SELECT id, name FROM user WHERE name=?", (contact_name,))
    result = cursor.fetchone()

    # If not found, check in `caretaker` table
    if not result:
        cursor.execute("SELECT id, name FROM caretaker WHERE name=?", (contact_name,))
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
    print(contact_number)
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

        # Fetch the contact's name using the phone number
        cursor.execute("SELECT name FROM contact WHERE contact_number=?", (str_contact_number,))
        contact_name = cursor.fetchone()[0]

        # Fetch the user ID and name from either `user` or `caretaker` table
        result = get_contact_info(contact_name)

        if not result:
            return "User not found", 404

        contact_id, contact_name = result  # Extract ID and Name

        # Fetch current user's name (Nareen)
        cursor.execute("SELECT name FROM user WHERE id=?", (user_id,))
        name = cursor.fetchone()[0]

        # Ensure user-specific folder exists
        user_folder = f"static/room_log/user/{user_id}/"
        os.makedirs(user_folder, exist_ok=True)

        # Define recipient's room file path (using contact's name)
        room_file_path = os.path.join(user_folder, f"{contact_name}.txt")

        room_number = None  # Initialize room_number variable

        # Check if a chat room file exists for this contact
        if os.path.exists(room_file_path):
            with open(room_file_path, "r") as file:
                lines = file.readlines()

            # Check if the current user already has a room with this contact
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
                file.write(f"{user_id}:{room_number}\n")   # Store Nareen's ID & room number
                file.write(f"{contact_id}:{room_number}\n")  # Store Contact's ID & room number
            
            # Also save in the contact’s folder (for Caretaker or User)
            contact_folder = f"static/room_log/user/{contact_id}/"
            os.makedirs(contact_folder, exist_ok=True)
            contact_room_file = os.path.join(contact_folder, f"{name}.txt")  # Save as "Nareen.txt"

            with open(contact_room_file, "w") as file:
                file.write(f"{contact_id}:{room_number}\n")   # Store Contact's ID & room number
                file.write(f"{user_id}:{room_number}\n")   # Store Nareen's ID & room number

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
    return "location user"

@app.route("/emergencyuser")
def emergencyuser():
    return "emergency user"

@app.route("/medicaluser")
def medicaluser():
    return "medical user"

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

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