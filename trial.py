import sqlite3
from flask import Flask, request, render_template, jsonify, g
import os

app = Flask(__name__)
DATABASE = "project.db"

# Function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Create Table if Not Exists
with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
    ''')
    db.commit()

# Route to Serve the Page
@app.route("/")
def index():
    return render_template("trial.html")

# Route to Receive Location Data
@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    user_id = data.get("user_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    if user_id and latitude and longitude:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO locations (user_id, latitude, longitude) VALUES (?, ?, ?)", (user_id, latitude, longitude))
        db.commit()
        return jsonify({"message": "Location updated successfully!"}), 200
    else:
        return jsonify({"error": "Invalid data"}), 400

# Route to Fetch All Locations
@app.route("/get_locations", methods=["GET"])
def get_locations():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, latitude, longitude FROM locations")
    locations = cursor.fetchall()
    location_data = [{"user_id": loc[0], "latitude": loc[1], "longitude": loc[2]} for loc in locations]
    return jsonify(location_data)

if __name__ == "__main__":
    app.run(debug=True)
