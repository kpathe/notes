from flask import Flask, render_template, request, redirect, session,flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Hash function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Routes
@app.route('/')
def home():
    if 'email' in session:
        return redirect('/index')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        
        if user and user[3] == hash_password(password):
            session['email'] = email
            conn.close()
            return redirect('/index')
        else:
            conn.close()
            return "Invalid email or password"

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            conn.close()
            flash('Email already signed up. Please log in.')
            return redirect('/login')

        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
        conn.commit()
        conn.close()

        # Create a new notes database for the user
        notes_db_name = f"{email.replace('@', '_').replace('.', '_')}_notes.db"
        conn = sqlite3.connect(notes_db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT,
                            content TEXT
                        )''')
        conn.commit()
        conn.close()
        
        return redirect('/login')

    return render_template('signup.html')


@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'email' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']

            # Retrieve the notes database name for the user
            notes_db_name = f"{session['email'].replace('@', '_').replace('.', '_')}_notes.db"

            conn = sqlite3.connect(notes_db_name)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            conn.commit()
            conn.close()
            return redirect('/index')

        # Retrieve the notes database name for the user
        notes_db_name = f"{session['email'].replace('@', '_').replace('.', '_')}_notes.db"

        conn = sqlite3.connect(notes_db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes")
        rows = cursor.fetchall()
        conn.close()
        print(rows)
        return render_template('index.html', email=session['email'], notes=rows)
    else:
        return redirect('/login')

@app.route('/delete', methods=['POST'])
def delete_note():
    if 'email' in session:
        # Retrieve the notes database name for the user
        notes_db_name = f"{session['email'].replace('@', '_').replace('.', '_')}_notes.db"

        # Connect to the user's notes database
        conn = sqlite3.connect(notes_db_name)
        cursor = conn.cursor()

        # Check if there are any notes in the database
        cursor.execute("SELECT COUNT(*) FROM notes")
        count = cursor.fetchone()[0]

        if count == 0:
            # If there are no notes, redirect to the index page
            conn.close()
            return redirect('/index')

        # Retrieve the ID of the last note
        cursor.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1")
        last_note_id = cursor.fetchone()[0]

        # Delete the last note
        cursor.execute("DELETE FROM notes WHERE id=?", (last_note_id,))
        conn.commit()
        
        # Close the database connection
        conn.close()

        # Redirect back to the index page
        return redirect('/index')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
