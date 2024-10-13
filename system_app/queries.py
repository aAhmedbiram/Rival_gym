from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret key'

# MySQL Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="gym_system_mysql"
)
cursor = conn.cursor()

DATABASE = 'gym_system_mysql'

# Replacing SQLite's `get_db` with MySQL connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=DATABASE
        )
    return db

def commit_close():
    db = getattr(g, '_database', None)
    if db is not None:
        db.commit()
        db.close()

# Create Table Function for MySQL
def create_table():
    # Note: You don't need to specify AUTO_INCREMENT explicitly here, as it's assumed for `PRIMARY KEY`
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INT PRIMARY KEY AUTO_INCREMENT,
        date DATE,
        member_id INT,
        member_name VARCHAR(100),
        status VARCHAR(50)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100),
        email VARCHAR(100),
        phone VARCHAR(50),
        age INT,
        gender VARCHAR(10),
        actual_starting_date DATE,
        starting_date DATE,
        end_date DATE,
        membership_packages VARCHAR(100),
        membership_fees DECIMAL(10, 2),
        membership_status VARCHAR(50)
    )""")
    conn.commit()

# Query the Database (Generalized Query Function for MySQL)
def query_db(query, args=(), one=False, order_by=None):
    cur = conn.cursor(dictionary=True)  # Using `dictionary=True` to return rows as dictionaries
    cur.execute(query, args)
    rv = cur.fetchall()  # Fetch all rows
    conn.commit()  # Commit any changes if needed

    if order_by and rv:
        rv = sorted(rv, key=lambda x: x[order_by], reverse=True)  # Sort by order key, reverse for DESC order

    # Return a single result if `one=True`, or the entire list
    return (rv[0] if rv else None) if one else rv

# Fetch attendance data without specific ordering
all_attendance_data = query_db("SELECT * FROM attendance", order_by=None)

# Check if a member name exists (for MySQL)
def check_name_exists(name):
    cursor.execute("SELECT COUNT(*) FROM members WHERE name = %s", (name,))
    count = cursor.fetchone()[0]
    return count > 0

# Check if an ID exists in members (for MySQL)
def check_id_exists(id_to_check):
    cursor.execute("SELECT COUNT(*) FROM members WHERE id = %s", (id_to_check,))
    count = cursor.fetchone()[0]
    return count > 0
