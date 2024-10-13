from flask import Flask, render_template, request, redirect, send_file, url_for,flash, session
from datetime import datetime,timedelta
import calendar
import sqlite3
from func import get_age_and_dob,add_member,calculate_age,calculate_end_date,membership_fees,compare_dates
from queries import create_table,query_db,check_name_exists,check_id_exists
# from werkzeug.security import check_password_hash, generate_password_hash
from queries import get_db,commit_close,query_db
from flask import jsonify
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
from mysql.connector import pooling

# from flask_bcrypt import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key='my secret key'

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'gym_system_mysql',
}
def get_connection():
    return connection_pool.get_connection()

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,  # Adjust the pool size based on your needs
    host='localhost',
    user='root',
    password='',
    database='gym_system_mysql'
)


UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = 'path/to/save/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    connection = mysql.connector.connect(**config)
    return connection


@app.route('/login')
@app.route('/')
def login():
    return render_template('login.html')


@app.route("/home")
def index():
    attendance_data = query_db('SELECT * FROM attendance')
    members_data = query_db('SELECT * FROM members')
    last_id = get_last_id()
    return render_template("index.html", attendance_data=attendance_data, members_data=members_data,last_id=last_id)

@app.route('/search', methods=['GET', 'POST'])
def search_by_name():
    if request.method == 'POST':
        name_to_check = request.form['name']
        exists = check_name_exists(name_to_check)
        if exists:
            with sqlite3.connect("gym_system.db") as conn:
                cr = conn.cursor()
                cr.execute("SELECT * FROM members WHERE name = ?", (name_to_check,))
                show_data = cr.fetchone()
                return render_template('result.html', name=name_to_check, data=show_data)
        else:
            return render_template('result.html', name=name_to_check, data=None)
    return render_template('search.html')

from flask import request, redirect, url_for, flash, jsonify
from datetime import datetime
import base64


from flask import request, redirect, url_for, flash
from datetime import datetime

@app.route("/add_member", methods=["POST"])
def add_member_route():
    if request.method == "POST":
        # Fetch form data
        member_name = request.form.get("member_name").capitalize()
        member_email = request.form.get("member_email")
        member_phone = request.form.get("member_phone")
        member_age = calculate_age(request.form.get("member_age"))
        member_gender = request.form.get("choice")
        member_birthdate = request.form.get("member_age")
        member_actual_starting_date = request.form.get("member_actual_starting_date")
        member_starting_date = request.form.get("member_starting_date")
        user_input = request.form.get("member_membership_packages")

        # Handle membership package parsing
        try:
            numeric_value, unit = user_input.split(maxsplit=1) if user_input else (None, None)
        except ValueError:
            numeric_value, unit = ("wrong package", "")

        # Calculate membership end date, fees, and status
        member_End_date = calculate_end_date(member_starting_date, numeric_value)
        member_membership_fees = membership_fees(user_input)
        member_membership_status = compare_dates(member_End_date)

        # Handle file upload (photo)
        file = request.files.get('file')
        file_data = None
        if file and file.filename != '':
            try:
                file_data = file.read()  # Read file content in binary mode
            except Exception as e:
                flash(f"Error reading file: {str(e)}")
                return redirect(url_for("index"))

        # Check if phone already exists
        existing_phones = query_db("SELECT phone FROM members")
        existing_phones_list = [phone['phone'] for phone in existing_phones]
        if member_phone in existing_phones_list:
            flash("Member with this phone number already exists")  # Flash the message
            return redirect(url_for("index"))  # Redirect to the index page

        # Call function to add new member
        new_member_id = add_member(
            member_name, 
            member_email, 
            member_phone, 
            member_age, 
            member_gender, 
            member_birthdate,
            member_actual_starting_date, 
            member_starting_date, 
            member_End_date,
            f"{numeric_value} {unit}", 
            member_membership_fees, 
            member_membership_status, 
            file_data  # Pass file data to the function
        )

        # Format dates for redirection
        try:
            parsed_actual_starting_date = datetime.strptime(member_actual_starting_date, '%Y-%m-%d')
            formatted_actual_starting_date = parsed_actual_starting_date.strftime('%m %d %Y')

            parsed_starting_date = datetime.strptime(member_starting_date, '%Y-%m-%d')
            formatted_starting_date = parsed_starting_date.strftime('%m %d %Y')
        except ValueError:
            flash("Invalid date format")
            return redirect(url_for("index"))

        # Redirect to confirmation page
        return redirect(url_for("add_member_done", new_member_id=new_member_id, 
                                formatted_actual_starting_date=formatted_actual_starting_date, 
                                formatted_starting_date=formatted_starting_date))
    
    return redirect(url_for("index"))

from datetime import datetime, date  # Ensure these imports are present

@app.route("/add_member_done/<int:new_member_id>")
def add_member_done(new_member_id):
    # Example to simulate fetching member data including a date
    member_data = query_db('SELECT actual_starting_date FROM members WHERE id = %s', (new_member_id,), one=True)

    if member_data and 'actual_starting_date' in member_data:
        actual_starting_date = member_data['actual_starting_date']  # Get the date from member data
        
        # Check if actual_starting_date is a string or date
        if isinstance(actual_starting_date, (date, datetime)):  # Handle both date and datetime
            formatted_date = actual_starting_date.strftime('%m/%d/%y')  # Format it to 'MM/DD/YY'
        else:
            # If it's a string, parse it
            parsed_date = datetime.strptime(actual_starting_date, '%Y-%m-%d')  # Adjust the format as necessary
            formatted_date = parsed_date.strftime('%m/%d/%y')  # Format it to 'MM/DD/YY'
    else:
        formatted_date = "Date not available"  # Set a default value if the date is not found

    return render_template("add_member_done.html", new_member_id=new_member_id, formatted_date=formatted_date)

@app.route("/show_member_data", methods=["POST"])
def show_member_data():
    if request.method == "POST":
        member_id = request.form.get("member_id")  # Get the member ID from the form

        # Query to fetch the member data by ID
        member_data = query_db('SELECT * FROM members WHERE id = %s', (member_id,), one=True)

        if member_data:
            # Format the dates if they exist in the member_data
            for date_field in ['actual_starting_date', 'starting_date']:
                if date_field in member_data:
                    if isinstance(member_data[date_field], (date, datetime)):
                        member_data[date_field] = member_data[date_field].strftime('%m/%d/%y')  # Format to 'MM/DD/YY'
                    else:
                        member_data[date_field] = datetime.strptime(member_data[date_field], '%Y-%m-%d').strftime('%m/%d/%y')  # Format to 'MM/DD/YY'

        # Render the member data in the template
        return render_template("show_member_data.html", member_data=member_data)
    
    return redirect(url_for("show_member_data"))



from flask import Response

@app.route('/image/<int:member_id>')
def get_image(member_id):
    # Fetch the image data from the database
    query = "SELECT id_img FROM members WHERE id = %s"
    result = query_db(query, (member_id,))
    
    if result:
        img_data = result[0]['id_img']  # Retrieve the image data
        if img_data:
            # Return the image as a response
            return Response(img_data, mimetype='image/jpeg')  # Adjust mimetype if necessary (e.g., 'image/png')
    
    # If no image data is found, return 404
    return "Image not found", 404

    

def query_db(query, args=(), one=False):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query, args)
        rv = cur.fetchall()
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None
    finally:
        cur.close()
        conn.close()  # Return the connection to the pool
    return (rv[0] if rv else None) if one else rv

ALLOWED_QUERIES = {
    "PRIMARY(ASC)": "SELECT * FROM members ORDER BY id ASC",
    "PRIMARY(DESC)": "SELECT * FROM members ORDER BY id DESC"
}

import base64

from flask import jsonify, render_template, request
import base64

ALLOWED_QUERIES = {
    "PRIMARY(ASC)": "SELECT * FROM members ORDER BY id ASC",
    "PRIMARY(DESC)": "SELECT * FROM members ORDER BY id DESC"
}

@app.route("/all_members", methods=['GET'])
def all_members():
    # Get the current page and the selected query key from the request
    page = request.args.get('page', 1, type=int)
    query_key = request.args.get('query', 'PRIMARY(ASC)')
    
    # Retrieve the SQL query based on the query key
    query = ALLOWED_QUERIES.get(query_key)
    if not query:
        return jsonify({"error": "Invalid query key"}), 400
    
    # Define pagination
    per_page = 10
    offset = (page - 1) * per_page
    
    # Add pagination to the SQL query
    query_with_pagination = f"{query} LIMIT %s OFFSET %s"
    
    # Execute the query with pagination
    members_data = query_db(query_with_pagination, (per_page, offset))
    
    # Convert binary image data (if exists) to Base64
    for member in members_data:
        if isinstance(member.get('id_img'), bytes):
            member['id_img'] = base64.b64encode(member['id_img']).decode('utf-8')  # Convert to Base64
    
    # If it's an AJAX request (infinite scroll), return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(members=members_data)
    
    # Render the full page for non-AJAX requests
    return render_template("all_members.html", members_data=members_data)


#################################################




@app.route("/edit_member/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id):
    if request.method == "GET":
        # Fetch the member data from the database using MySQL
        member = query_db('SELECT * FROM members WHERE id = %s', (member_id,), one=True)
        return render_template("edit_member.html", member=member)
    
    elif request.method == "POST":
        # Get data from the form
        edit_member_name = request.form.get("edit_member_name").capitalize()
        edit_member_email = request.form.get("edit_member_email")
        edit_member_phone = request.form.get("edit_member_phone")
        edit_member_age = calculate_age(request.form.get("edit_member_age"))
        member_gender = request.form.get("edit_member_gender")
        edit_actual_starting_date = request.form.get("edit_actual_starting_date")
        edit_starting_date = request.form.get("edit_starting_date")
        
        # Handle membership packages input
        user_input = request.form.get("edit_membership_packages")
        try:
            numeric_value, unit = user_input.split(maxsplit=1) if user_input else (None, None)
        except ValueError:
            numeric_value, unit = ("wrong package", "")
        
        # Calculate the end date, membership fees, and status
        member_End_date = calculate_end_date(edit_starting_date, numeric_value)
        member_membership_fees = membership_fees(user_input)
        member_membership_status = compare_dates(member_End_date)

        # Establish a MySQL connection
        from app import get_db_connection  # Make sure get_db_connection connects to MySQL
        conn = get_db_connection()
        cur = conn.cursor()

        # Update the member record in the MySQL database
        cur.execute('''
            UPDATE members 
            SET name = %s, email = %s, phone = %s, age = %s, gender = %s, actual_starting_date = %s, 
                starting_date = %s, End_date = %s, membership_packages = %s, membership_fees = %s, membership_status = %s 
            WHERE id = %s
        ''', 
        (
            edit_member_name, edit_member_email, edit_member_phone, edit_member_age, member_gender, edit_actual_starting_date,
            edit_starting_date, member_End_date, f"{numeric_value} {unit}", member_membership_fees, member_membership_status, member_id
        ))

        conn.commit()  # Commit changes
        cur.close()    # Close the cursor
        conn.close()   # Close the connection

        # Redirect to index after updating
        return redirect(url_for("index"))




@app.route("/search_by_mobile_number", methods=["POST"])
def search_by_mobile_number():
    if request.method == "POST":
        # Get the phone number from the form
        member_phone = request.form.get("member_phone")

        # Query the database using the MySQL parameterized query style (%s)
        member_data = query_db('SELECT * FROM members WHERE phone = %s', (member_phone,), one=True)

        # Render the result_phone.html template and pass the member data
        return render_template("result_phone.html", member_data=member_data)

    # If not a POST request, redirect to the result_phone page
    return redirect(url_for("result_phone"))


@app.route("/result_phone", methods=["POST"])
def result_phone():
    if request.method == "POST":
        member_phone = request.form.get("member_phone")
        member_data = query_db('SELECT * FROM members WHERE phone = ?', (member_phone,), one=True)
        return render_template("result_phone.html", member_data=member_data)
    return redirect(url_for("result_phone"))

@app.route("/result", methods=["POST"])
def result():
    if request.method == "POST":
        # Get the member name from the form and capitalize it
        member_name = request.form.get("member_name").capitalize()

        # Query the database to get member data using MySQL's parameterized query style
        member_data = query_db('SELECT * FROM members WHERE name = %s', (member_name,), one=True)

        # Render the result.html template and pass member data
        return render_template("result.html", member_data=member_data)
    
    # If not a POST request, redirect to the result page
    return redirect(url_for("result"))

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('gym_system.db')
    cr = conn.cursor()
    cr.execute('''
        SELECT * FROM users
        WHERE username = ? 
    ''', (username,))
    result = cr.fetchone()
    conn.close()
    if result and result[3] == password:
        session['username'] = result[0]
        flash('success signup successful', 'success')
        return redirect(url_for('index', username=username))
    else:
        flash('error Incorrect username or password', 'error')
        return redirect(url_for('login'))
    
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session data to log the user out
    session.clear()
    flash('success Logged out successfully', 'success')
    return render_template("logout.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('gym_system.db')
        cr = conn.cursor()
        try:
            cr.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, password))
            conn.commit()
            flash('success User created successfully', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('error Username or email already exists. Please choose another.', 'error')
        conn.close()
    return render_template('signup.html')

@app.route('/change_password', methods=['POST', 'GET'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            app.logger.info(f"user: {user}")  # Debug print
            stored_password = user[3]  # Adjust the index based on your database structure
            app.logger.info(f"stored_password: {stored_password}")  # Debug print

            if old_password == stored_password:
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
                commit_close()
                flash('success Password successfully changed!')
                return redirect(url_for('success'))
            else:
                error_message = "Invalid old password"
        else:
            error_message = "Invalid username"

        app.logger.error(f"Error changing password: {error_message}")  # Debug print
        return render_template('change_password.html', error_message=error_message)

    return render_template('change_password.html')

def update_attendance(member_id):
    global current_date,current_day,current_time
    member_data = get_member_data(member_id)
    if member_data:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")

        query = "INSERT INTO attendance (num, id, name, end_date, membership_status, attendance_time, attendance_date, day) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        get_db().execute(query, (member_data['num'], member_data['id'], member_data['name'], member_data['end_date'],
                                member_data['membership_status'], current_time, current_date, current_day))
        get_db().commit()

def get_member_data(member_id):
    query = f"SELECT * FROM members WHERE id = {member_id}"
    return query_db(query, one=True)

@app.route('/attendance_table', methods=['GET', 'POST'])
def attendance_table():
    get_db_connection()
    current_time = ""
    current_date = ""
    current_day = ""
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        query = f"SELECT * FROM members WHERE id = {member_id}"
        cursor = get_db().cursor()
        cursor.execute(query)
        row = cursor.fetchone()
        

        if row:
            columns = [col[0] for col in cursor.description]
            member_data = dict(zip(columns, row))
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date = now.strftime("%Y-%m-%d")
            current_day = now.strftime("%A")

            # Update or insert data into the first table (attendance)
            existing_data = query_db(f"SELECT * FROM attendance WHERE id = {member_data['id']}")
            if existing_data:
                update_query = f"UPDATE attendance SET name = '{member_data['name']}', " \
                                f"end_date = '{member_data['End_date']}', " \
                                f"membership_status = '{member_data['membership_status']}', " \
                                f"attendance_time = '{current_time}', " \
                                f"attendance_date = '{current_date}', " \
                                f"day = '{current_day}' WHERE id = {member_data['id']}"
                cursor.execute(update_query)
            else:
                insert_query = f"INSERT INTO attendance (id, name, end_date, membership_status, " \
                                f"attendance_time, attendance_date, day) VALUES ({member_data['id']}, " \
                                f"'{member_data['name']}', '{member_data['End_date']}', " \
                                f"'{member_data['membership_status']}', '{current_time}', " \
                                f"'{current_date}', '{current_day}')"
                cursor.execute(insert_query)

            # Insert data into the second table (attendance_backup)
            insert_query_backup = f"INSERT INTO attendance_backup (id, name, end_date, membership_status, " \
                                f"attendance_time, attendance_date, day) VALUES ({member_data['id']}, " \
                                f"'{member_data['name']}', '{member_data['End_date']}', " \
                                f"'{member_data['membership_status']}', '{current_time}', " \
                                f"'{current_date}', '{current_day}')"
            cursor.execute(insert_query_backup)

            get_db().commit()
            session.setdefault('members_data', []).append(member_data)
    
    all_attendance_data = query_db("SELECT * FROM attendance ORDER BY num asc", order_by=None)
    return render_template("attendance_table.html", members_data=all_attendance_data)


@app.route('/delete_all_data', methods=['POST'])
def delete_all_data():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Step 1: Backup data
        backup_query = "INSERT IGNORE INTO attendance_backup SELECT * FROM attendance;"
        cursor.execute(backup_query)

        # Step 2: Commit the backup
        connection.commit()

        # Step 3: Delete all records from attendance
        delete_query = "DELETE FROM attendance;"
        cursor.execute(delete_query)

        # Step 4: Commit the delete
        connection.commit()

    except Error as e:
        print("Error:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect(url_for('attendance_table'))

@app.route('/success')
def success():
    return render_template('success.html')



def get_last_id():
    # Connect to the MySQL database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Define the query to get the row with the maximum id
    last_id_query = """
    SELECT * 
    FROM members 
    WHERE id = (SELECT MAX(id) FROM members);
    """

    # Execute the query
    cursor.execute(last_id_query)

    # Fetch the result
    result = cursor.fetchone()  # Use fetchall() if you expect multiple rows

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return result[0] if result else None
# #####################################################################################



# ######################################################################################



if __name__ == "__main__":
    app.run(debug=True)
