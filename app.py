import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
import bcrypt
from datetime import datetime

# Import models
from models.emotion import detect_emotion
from models.recommender import get_recommendations, track_interaction

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- AUTH ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- MAIN ROUTES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Process image from webcam
    image_data = request.json.get('image')
    emotion = detect_emotion(image_data)
    
    # Save mood to DB
    conn = get_db_connection()
    conn.execute('INSERT INTO moods (user_id, emotion) VALUES (?, ?)', (session['user_id'], emotion))
    conn.commit()
    conn.close()
    
    return jsonify({'emotion': emotion})

@app.route('/recommendations/<emotion>')
def recommendations(emotion):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    songs = get_recommendations(session['user_id'], emotion)
    return jsonify({'songs': songs})

@app.route('/track', methods=['POST'])
def track():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    track_interaction(session['user_id'], data['song_id'], data['song_title'], data['action'])
    return jsonify({'status': 'success'})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Mood distribution
    moods = conn.execute('SELECT emotion, COUNT(*) as count FROM moods WHERE user_id = ? GROUP BY emotion', (session['user_id'],)).fetchall()
    
    # Most played
    top_songs = conn.execute('SELECT song_title, COUNT(*) as count FROM interactions WHERE user_id = ? AND action = "play" GROUP BY song_id ORDER BY count DESC LIMIT 5', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', moods=[dict(m) for m in moods], top_songs=[dict(s) for s in top_songs])

if __name__ == '__main__':
    app.run(debug=True)
