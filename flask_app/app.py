from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Create data directory if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Create users.csv if it doesn't exist
if not os.path.exists('data/users.csv'):
    with open('data/users.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'email', 'password', 'age', 'weight', 'height'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def landing():
    if 'username' in session:
        return redirect(url_for('profile'))
    return render_template("landing.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with open('data/users.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username and check_password_hash(row['password'], password):
                    session['username'] = username
                    return redirect(url_for('profile'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        age = request.form['age']
        weight = request.form['weight']
        height = request.form['height']
        
        # Check if passwords match
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        
        # Check if username already exists
        with open('data/users.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username:
                    return render_template('signup.html', error='Username already exists')
        
        # Hash password and save user
        hashed_password = generate_password_hash(password)
        with open('data/users.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, email, hashed_password, age, weight, height])
        
        session['username'] = username
        return redirect(url_for('profile'))
    
    return render_template('signup.html')

@app.route("/profile")
@login_required
def profile():
    username = session['username']
    with open('data/users.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == username:
                user = {
                    'username': row['username'],
                    'email': row['email'],
                    'age': row['age'],
                    'weight': row['weight'],
                    'height': row['height']
                }
                return render_template('profile.html', user=user)
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('landing'))

@app.route("/trainer")
@login_required
def index():
    return render_template("index.html")

if __name__ == "__main__":
    # Run on all network interfaces so you can use your phone
    app.run(host="0.0.0.0", port=5050, debug=True)
