from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

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
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get user information from users.csv
    user_info = None
    with open('data/users.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == session['username']:
                user_info = {
                    'username': row['username'],
                    'email': row['email'],
                    'age': row['age'],
                    'weight': row['weight'],
                    'height': row['height']
                }
                break
    
    if not user_info:
        return redirect(url_for('login'))
    
    # Read workout history from summary.csv
    workout_history = []
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'summary.csv')
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Convert time to minutes and seconds
                    total_seconds = float(row['Total Time (s)'])
                    minutes = int(total_seconds // 60)
                    seconds = int(total_seconds % 60)
                    time_str = f"{minutes}m {seconds}s"
                    
                    workout_history.append({
                        'sets_completed': row['Sets Completed'],
                        'sets_missed': row['Sets Missed'],
                        'total_reps': row['Total Reps'],
                        'duration': time_str,
                        'mistakes': row['Mistakes']
                    })
                except (ValueError, KeyError) as e:
                    # Skip invalid rows
                    continue
    
    # Sort workout history by most recent first (assuming newest entries are at the bottom of the file)
    workout_history.reverse()
    
    return render_template("profile.html", user=user_info, workout_history=workout_history)

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('landing'))

@app.route("/trainer")
@login_required
def index():
    return render_template("index.html")

@app.route('/save_workout_summary', methods=['POST'])
def save_workout_summary():
    try:
        data = request.get_json()
        csv_content = data.get('csv_content')
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Path to the summary file
        summary_file = os.path.join(data_dir, 'summary.csv')
        
        # Write header only if file doesn't exist
        if not os.path.exists(summary_file):
            with open(summary_file, 'w') as f:
                f.write('Sets Completed,Sets Missed,Total Reps,Total Time (s),Mistakes\n')
        
        # Append the workout data
        with open(summary_file, 'a') as f:
            f.write(csv_content + '\n')
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving workout summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == "__main__":
    # Run on all network interfaces so you can use your phone
    app.run(host="0.0.0.0", port=5050, debug=True)
