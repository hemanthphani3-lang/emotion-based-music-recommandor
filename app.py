import os
from typing import Dict, Any, List, Optional, Union

import bcrypt  # type: ignore
from flask import (  # type: ignore
    Flask, render_template, request, redirect, url_for, session, jsonify,
    Response
)
from flask_session import Session  # type: ignore

# Import models
from models.emotion import detect_emotion  # type: ignore
from models.recommender import get_recommendations, track_interaction  # type: ignore
from models.db import supabase  # type: ignore

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# --- AUTH ROUTES ---


@app.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, Response]:
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            supabase.table('users').insert({
                "username": username,
                "password": hashed.decode('utf-8')
            }).execute()
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Registration Error: {e}")
            return f"Username already exists or an error occurred: {e}"

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, Response]:
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        user_response = supabase.table('users').select(
            '*'
        ).eq('username', username).execute()

        user_data: List[Dict[str, Any]] = getattr(user_response, 'data', [])
        user: Optional[Dict[str, Any]] = (
            user_data[0] if user_data and len(user_data) > 0 else None
        )

        if isinstance(user, dict) and bcrypt.checkpw(
            password.encode('utf-8'),
            user.get('password', '').encode('utf-8')
        ):
            session['user_id'] = user.get('id')
            session['username'] = user.get('username')
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"

    return render_template('login.html')


@app.route('/logout')
def logout() -> Response:
    session.clear()
    return redirect(url_for('login'))


# --- MAIN ROUTES ---


@app.route('/')
def index() -> Union[str, Response]:
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/detect', methods=['POST'])
def detect() -> Response:
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # Process image from webcam
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400

    image_data = data.get('image', '')
    emotion = detect_emotion(image_data)

    # Save mood to DB
    try:
        supabase.table('moods').insert({
            "user_id": session['user_id'],
            "emotion": emotion
        }).execute()
    except Exception as e:
        print(f"Error saving mood: {e}")

    return jsonify({'emotion': emotion})


@app.route('/recommendations/<emotion>')
def recommendations(emotion: str) -> Response:
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    songs = get_recommendations(session['user_id'], emotion)
    return jsonify({'songs': songs})


@app.route('/track', methods=['POST'])
def track() -> Response:
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid request'}), 400

    track_interaction(
        session['user_id'],
        data.get('song_id', ''),
        data.get('song_title', 'Unknown'),
        data.get('action', 'play')
    )
    return jsonify({'status': 'success'})


@app.route('/dashboard')
def dashboard() -> Union[str, Response]:
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Mood distribution
    moods_response = supabase.table('moods').select('emotion').eq(
        'user_id', session['user_id']
    ).execute()

    mood_counts: Dict[str, int] = {}
    for m in getattr(moods_response, 'data', []):
        if isinstance(m, dict):
            emo = m.get('emotion', 'Neutral')
            mood_counts[emo] = mood_counts.get(emo, 0) + 1

    moods = [{'emotion': k, 'count': v} for k, v in mood_counts.items()]

    # Most played top 5
    top_response = supabase.table('interactions').select(
        'song_id, song_title'
    ).eq(
        'user_id', session['user_id']
    ).eq('action', 'play').execute()

    song_counts: Dict[str, int] = {}
    song_titles: Dict[str, str] = {}

    data: List[Dict[str, Any]] = getattr(top_response, 'data', [])
    for t in data:
        if isinstance(t, dict):
            sid = t.get('song_id')
            if not sid:
                continue
            song_counts[sid] = song_counts.get(sid, 0) + 1
            song_titles[sid] = t.get('song_title', 'Unknown')

    sorted_items = sorted(
        song_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_songs = []
    for count_index, (sid, count) in enumerate(sorted_items):
        if count_index >= 5:
            break
        title = song_titles.get(sid, "Unknown")
        top_songs.append({'song_title': title, 'count': count})

    return render_template('dashboard.html', moods=moods, top_songs=top_songs)


if __name__ == '__main__':
    app.run(debug=True)
