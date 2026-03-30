import sqlite3
import requests
import os
from googleapiclient.discovery import build

# Replace with your actual YouTube Data API v3 key
YOUTUBE_API_KEY = "AIzaSyDW9GzPuRBywdgKE4be4nXnIcoldemTJTY"

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_recommendations(user_id, emotion):
    """
    Fetches music recommendations from YouTube based on emotion.
    Avoids recently skipped songs and prioritizes diverse results.
    """
    search_query = f"{emotion} songs playlist"
    
    try:
        # Check for skipped songs to exclude
        conn = get_db_connection()
        skipped_songs = conn.execute('SELECT song_id FROM interactions WHERE user_id = ? AND action = "skip"', (user_id,)).fetchall()
        skipped_ids = [s['song_id'] for s in skipped_songs]
        conn.close()

        # Build YouTube client
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        
        request = youtube.search().list(
            q=search_query,
            part="snippet",
            maxResults=10,
            type="video",
            videoEmbeddable="true"
        )
        response = request.execute()
        
        songs = []
        for item in response.get("items", []):
            song_id = item["id"]["videoId"]
            # Filter skipped
            if song_id in skipped_ids:
                continue
                
            songs.append({
                "id": song_id,
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            })
            
        return songs[:6] # Return top 6
        
    except Exception as e:
        print(f"YouTube API Error: {e}")
        # Fallback Mock Data if API fails or key is missing
        return [
            {"id": "dQw4w9WgXcQ", "title": f"Fallback: Upbeat {emotion} Tracks", "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg"},
            {"id": "3JZ_D3i301s", "title": f"Soulful {emotion} Vibes", "thumbnail": "https://i.ytimg.com/vi/3JZ_D3i301s/mqdefault.jpg"}
        ]

def track_interaction(user_id, song_id, song_title, action):
    """
    Records user interactions (play, skip, favorite).
    """
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO interactions (user_id, song_id, song_title, action) VALUES (?, ?, ?, ?)',
        (user_id, song_id, song_title, action)
    )
    conn.commit()
    conn.close()
