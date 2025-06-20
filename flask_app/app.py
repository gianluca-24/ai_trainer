from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import csv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

if not os.path.exists('data'):
    os.makedirs('data')

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

        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')

        with open('data/users.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username:
                    return render_template('signup.html', error='Username already exists')

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

    user_info = None
    with open('data/users.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['username'] == session['username']:
                user_info = {
                    'username': row['username'],
                    'email': row['email'],
                    'age': row['age'],
                    'height': row['height'],
                    'weight': row['weight']
                }
                break

    if not user_info:
        return redirect(url_for('login'))

    workout_history = []
    summary_file = 'data/summary.csv'
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('username') != session['username']:
                    continue
                try:
                    total_seconds = float(row['Total Time (s)'])
                    minutes = int(total_seconds // 60)
                    seconds = int(total_seconds % 60)
                    duration = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

                    workout = {
                        'date': row.get('date', 'N/A'),
                        'sets_completed': row.get('Sets Completed', '0'),
                        'sets_missed': row.get('Sets Missed', '0'),
                        'total_reps': row.get('Total Reps', '0'),
                        'duration': duration,
                        'mistakes': row.get('Mistakes', ''),
                        'score': row.get('Score', '0'),
                        'supersets': row.get('Supersets', '0')
                    }
                    workout_history.append(workout)
                except (ValueError, KeyError):
                    continue

    # Global and Personal score logic
    global_scores_raw = {}
    personal_best = {'score': 0, 'date': None}

    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    score = int(row.get('Score', 0))
                    username = row.get('username')
                    date = row.get('date', 'N/A')

                    # Global
                    if username not in global_scores_raw or score > global_scores_raw[username]['score']:
                        global_scores_raw[username] = {'username': username, 'score': score}

                    # Personal
                    if username == session['username'] and score > personal_best['score']:
                        personal_best['score'] = score
                        personal_best['date'] = date
                except ValueError:
                    continue

    global_scores = sorted(global_scores_raw.values(), key=lambda x: x['score'], reverse=True)[:3]
    workout_history.reverse()

    return render_template(
        'profile.html',
        user=user_info,
        workout_history=workout_history,
        global_scores=global_scores,
        personal_best=personal_best
    )

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('landing'))

@app.route("/trainer")
@login_required
def index():
    return render_template("index.html")

@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    section = request.form.get("section")
    current_username = session["username"]
    fieldnames = ["username", "email", "password", "age", "weight", "height"]
    user_file = "data/users.csv"

    users = []
    updated = False

    with open(user_file, "r", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for field in fieldnames:
                if field not in row:
                    row[field] = ""

            if row["username"] == current_username:
                if section == "personal":
                    email = request.form.get("email")
                    age = request.form.get("age")
                    current_password = request.form.get("current_password")
                    new_password = request.form.get("new_password")
                    confirm_password = request.form.get("confirm_password")

                    if email:
                        row["email"] = email
                    if age:
                        row["age"] = age

                    if new_password or confirm_password:
                        if not current_password:
                            flash("Please enter your current password to change it.", "danger")
                            return redirect(url_for("profile"))

                        if not check_password_hash(row["password"], current_password):
                            flash("Current password is incorrect.", "danger")
                            return redirect(url_for("profile"))

                        if new_password != confirm_password:
                            flash("New passwords do not match.", "danger")
                            return redirect(url_for("profile"))

                        row["password"] = generate_password_hash(new_password)

                elif section == "physical":
                    height = request.form.get("height")
                    weight = request.form.get("weight")
                    if height:
                        row["height"] = height
                    if weight:
                        row["weight"] = weight

                updated = True

            users.append(row)

    if updated:
        with open(user_file, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)
        flash("Profile updated successfully.", "success")
    else:
        flash("User not found or update failed.", "danger")

    return redirect(url_for("profile"))

@app.route('/save_workout_summary', methods=['POST'])
@login_required
def save_workout_summary():
    try:
        data = request.get_json()
        csv_content = data.get('csv_content')
        username = session['username']
        current_date = datetime.now().strftime('%Y-%m-%d')

        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        summary_file = os.path.join(data_dir, 'summary.csv')

        file_exists = os.path.isfile(summary_file)

        with open(summary_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['username', 'date', 'Sets Completed', 'Sets Missed', 'Total Reps', 'Total Time (s)', 'Mistakes', 'Score', 'Supersets'])
            row = [username, current_date] + csv_content.split(',')
            writer.writerow(row)

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving workout summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
