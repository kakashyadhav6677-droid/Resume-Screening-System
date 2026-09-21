from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import MySQLdb.cursors
from PyPDF2 import PdfReader
from docx import Document
from flask import send_from_directory
from flask import send_file


app = Flask(__name__)
app.secret_key = 'your_secret_key_12345'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'akash@2830'
app.config['MYSQL_DB'] = 'resume_screening'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    msg=''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        role = request.form['role']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        else:
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)',
                           (username, email, hashed_password, role))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            session['loggedin'] = True
            session['id'] = cursor.lastrowid
            session['username'] = username
            session['role'] = role

            if role == 'employer':
                return redirect(url_for('employer_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))

    return render_template('index.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account and bcrypt.check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['role'] = account['role']

            if account['role'] == 'employer':
                return redirect(url_for('employer_dashboard'))
            else:
                return redirect(url_for('create_employee_profile'))
        else:
            msg = 'Incorrect email/password!'

    return render_template('login.html')

@app.route('/employer_dashboard')
def employer_dashboard():
    if 'loggedin' in session and session['role'] == 'employer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM jobs WHERE employer_id = %s', [session['id']])
        jobs = cursor.fetchall()
        return render_template('employer_dashboard.html', username=session['username'], jobs=jobs)
    else:
        # If not logged in or not an employer, redirect to the login page
        return redirect(url_for('login'))

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if 'loggedin' in session and session['role'] == 'employer':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM employers WHERE user_id = %s', [session['id']])
        profile = cursor.fetchone()

        if request.method == 'POST':
            company_name = request.form['company_name']
            industry = request.form['industry']
            location = request.form['location']
            contact_email = request.form['contact_email']
            contact_phone = request.form['contact_phone']
            gender = request.form['gender']
            website = request.form['website']
            company_description = request.form['company_description']

            if profile:
                # Update existing profile
                cursor.execute('''
                    UPDATE employers
                    SET company_name=%s, industry=%s, location=%s, contact_email=%s, contact_phone=%s, gender=%s, website=%s, company_description=%s
                    WHERE user_id=%s
                ''', (company_name, industry, location, contact_email, contact_phone, gender, website, company_description, session['id']))
                mysql.connection.commit()
                flash('Profile updated successfully!', 'success')
            else:
                # Create a new profile if it doesn't exist
                cursor.execute('''
                    INSERT INTO employers (user_id, company_name, industry, location, contact_email, contact_phone, gender, website, company_description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (session['id'], company_name, industry, location, contact_email, contact_phone, gender, website, company_description))
                mysql.connection.commit()
                flash('Profile created successfully!', 'success')
            return redirect(url_for('employer_dashboard'))

        return render_template('create_profile.html', profile=profile)
    return redirect(url_for('login'))


@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'loggedin' in session and session['role'] == 'employer':
        if request.method == 'POST':
            job_title = request.form['job_title']
            job_description = request.form['job_description']
            keywords = request.form['keywords']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO jobs (employer_id, job_title, job_description, keywords) VALUES (%s, %s, %s, %s)',
                           (session['id'], job_title, job_description, keywords))
            mysql.connection.commit()
            return redirect(url_for('employer_dashboard'))
        return render_template('post_job.html')
    return redirect(url_for('login'))
    
    # Ensure upload folder exists
UPLOAD_FOLDER = "D:\\Resume-Screening-System\\static\\uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
print(UPLOAD_FOLDER)

# Set the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Employee Profile Route
@app.route('/create_employee_profile', methods=['GET', 'POST'])
def create_employee_profile():
    if 'loggedin' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the employee already has a profile
    cursor.execute("SELECT * FROM employees WHERE user_id = %s", (session['id'],))
    profile = cursor.fetchone()

    if request.method == 'POST':
        full_name = request.form['full_name']
        location = request.form['location']
        contact_email = request.form['contact_email']
        contact_phone = request.form['contact_phone']
        cover_letter = request.form.get('cover_letter')  # Get cover letter content from form

        # Handle resume file upload
        resume = request.files['resume']
        resume_path = ""
        if resume:
            resume_filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
            resume.save(resume_path)
            resume_path = f"{resume_filename}"  # Store relative path instead
            flash(f"An error occurred: flash message", 'danger')

        # Handle cover letter file upload
        cover_letter_file = request.files.get('cover_letter_file')
        cover_letter_path = None
        if cover_letter_file:
            cover_letter_filename = secure_filename(cover_letter_file.filename)
            cover_letter_path = os.path.join(app.config['UPLOAD_FOLDER'], cover_letter_filename)
            cover_letter_file.save(cover_letter_path)

        if profile:
            # Update existing profile
            cursor.execute("""
                UPDATE employees 
                SET full_name = %s, location = %s, contact_email = %s, contact_phone = %s, 
                    cover_letter = %s, cover_letter_path = %s
                WHERE user_id = %s
            """, (full_name, location, contact_email, contact_phone, cover_letter, cover_letter_path, session['id']))
            #print("before psth" + resume_path)
            if resume_path != "":
                #print("sfter print" + resume_path)
                cursor.execute("""
                UPDATE employees 
                SET resume_path = %s
                WHERE user_id = %s
            """, (resume_path, session['id']))
            flash('Profile updated successfully!', 'success')
        else:
            # Insert new profile
            cursor.execute("""
                INSERT INTO employees (user_id, full_name, location, contact_email, contact_phone, 
                                       resume_path, cover_letter, cover_letter_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['id'], full_name, location, contact_email, contact_phone, resume_path, cover_letter, cover_letter_path))
            flash('Profile created successfully!', 'success')

        mysql.connection.commit()
        return redirect(url_for('employee_dashboard'))

    # Render profile page for editing or creating
    return render_template('create_employee_profile.html', profile=profile)

@app.route('/employee_dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    # Ensure the user is logged in and is an employee
    if 'loggedin' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))

    # Initialize the cursor
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the employee has a profile
    cursor.execute("SELECT * FROM employees WHERE user_id = %s", (session['id'],))
    profile = cursor.fetchone()

    if not profile:
        # Redirect new users to profile creation if no profile exists
        return redirect(url_for('create_employee_profile'))

    # Job search functionality
    if request.method == 'POST':
        search_query = request.form.get('search')
        cursor.execute("""
            SELECT id AS job_id, job_title, job_description, date_posted 
            FROM jobs 
            WHERE job_title LIKE %s OR job_description LIKE %s
        """, ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        # Fetch all available jobs
        cursor.execute("SELECT id AS job_id, job_title, job_description, date_posted FROM jobs")

    # Fetch the job results
    jobs = cursor.fetchall()

    return render_template('employee_dashboard.html', jobs=jobs, profile=profile)

# Job Application apply
@app.route('/apply/<int:job_id>', methods=['POST'])
def apply(job_id):
    if 'loggedin' in session and session['role'] == 'employee':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        print("step-1")

        # Fetch the employee's profile ID and resume path
        cursor.execute("SELECT id, resume_path FROM employees WHERE user_id = %s", (session['id'],))
        employee = cursor.fetchone()
        print("step-2")
        if employee:
            employee_id = employee['id']
            resume_path = employee['resume_path']
            print("step-3")
            print(resume_path)
            # Fetch the job keywords
            cursor.execute("SELECT job_title, keywords FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            print("step-4")
            if job and resume_path:
                job_keywords = job['keywords']
                resume_text = extract_text_from_file(os.path.join(app.config['UPLOAD_FOLDER'], resume_path))  # Corrected path

                if resume_text:
                    score, matched_keywords = calculate_resume_score(resume_text, job_keywords)
                    print("resume score",score)
                    # Save the application and score to the database
                    cursor.execute("""
                        INSERT INTO applications (employee_id, job_id, score)
                        VALUES (%s, %s, %s)
                    """, (employee_id, job_id, score))
                    mysql.connection.commit()

                    flash(f'Application submitted! Your resume matched {len(matched_keywords)} keywords. Your score: {score}.', 'success')
                    # Pass job_id to the template for rendering
                    return redirect(url_for('employee_dashboard', job_id=job_id))
                else:
                    flash('Error reading your resume. Please upload a valid file.', 'danger')
            else:
                flash('Job not found or resume missing.', 'danger')
        else:
            flash('Please complete your profile before applying for jobs.', 'danger')

        return redirect(url_for('employee_dashboard'))
    else:
        flash('You must be logged in to apply for a job.', 'danger')
        return redirect(url_for('login'))

#Job Applications Route
@app.route('/view_resume/<path:resume_path>')
def view_resume(resume_path):
    try:
        # Ensure the file exists in the specified location
        return send_file(resume_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404

@app.route('/job_applications/<int:job_id>')
def job_applications(job_id):
    # Ensure the user is logged in and is an employer
    if 'loggedin' not in session or session['role'] != 'employer':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch job applications for the given job ID, sorted by score
    cursor.execute("""
        SELECT a.id AS application_id, e.full_name AS name, e.contact_email AS contact_email, 
               a.score AS score, e.resume_path AS resume_path, a.application_date AS application_date
        FROM applications a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.job_id = %s
        ORDER BY a.score DESC
    """, (job_id,))
    applications = cursor.fetchall()  # List of applications for the job

    return render_template('job_applications.html', applications=applications, job_id=job_id)

#Extract text from resume
def extract_text_from_file(file_path):
    text = ""
    if file_path.endswith('.pdf'):
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
    elif file_path.endswith('.docx'):
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text
        except Exception as e:
            print(f"Error reading DOCX: {e}")
    return text

#Resume Screening Logic
def calculate_resume_score(resume_text, job_keywords):
    job_keywords = set(job_keywords.lower().split())  # Convert keywords to lowercase and split
    resume_words = set(resume_text.lower().split())   # Convert resume text to lowercase and split
    matched_keywords = job_keywords.intersection(resume_words)
    return len(matched_keywords), matched_keywords

#view resume
"""@app.route('/view_resume/<path:resume_path>')
def view_resume(resume_path):
    try:
        # Adjust to use the 'static/uploads' path
        return send_from_directory(app.config['UPLOAD_FOLDER'], resume_path)  # Corrected file path
    except FileNotFoundError:
        return "Resume not found", 404"""

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)