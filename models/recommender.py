import random
from typing import List, Dict, Any
from googleapiclient.discovery import build  # type: ignore
from .db import supabase  # type: ignore

# Replace with your actual YouTube Data API v3 key
YOUTUBE_API_KEY = "AIzaSyDW9GzPuRBywdgKE4be4nXnIcoldemTJTY"


def get_recommendations(user_id: str, emotion: str) -> List[Dict[str, Any]]:
    """
    Fetches music recommendations from YouTube based on emotion.
    Avoids recently skipped songs and prioritizes diverse results.
    """
    search_query = f"{emotion} songs playlist"

    try:
        # Check for user preferences
        pref_response = supabase.table('user_preferences').select('languages, artists').eq('user_id', user_id).execute()
        prefs = getattr(pref_response, 'data', [])
        if prefs and len(prefs) > 0:
            user_pref = prefs[0]
            langs = user_pref.get('languages', [])
            arts = user_pref.get('artists', [])
            
            query_parts = []
            if langs:
                query_parts.append(random.choice(langs))
            query_parts.append(emotion)
            query_parts.append("songs")
            if arts:
                query_parts.append(random.choice(arts))
            
            if len(query_parts) > 2:
                search_query = " ".join(query_parts)
                print(f"Personalized search query: {search_query}")

        # Check for skipped songs to exclude using Supabase
        response = supabase.table('interactions').select('song_id').eq(
            'user_id', user_id
        ).eq('action', 'skip').execute()

        data: List[Dict[str, Any]] = getattr(response, 'data', [])
        skipped_ids = [s.get('song_id') for s in data if isinstance(s, dict)]

        # Build YouTube client
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        request = youtube.search().list(
            q=search_query,
            part="snippet",
            maxResults=10,
            type="video",
            videoEmbeddable="true",
            videoSyndicated="true"
        )
        api_response = request.execute()

        items = []
        if isinstance(api_response, dict):
            items = api_response.get("items", [])

        songs: List[Dict[str, Any]] = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue

            id_dict = raw_item.get("id", {})
            if not isinstance(id_dict, dict):
                continue
            song_id = id_dict.get("videoId")

            if not song_id or song_id in skipped_ids:
                continue

            snippet = raw_item.get("snippet", {})
            if not isinstance(snippet, dict):
                continue

            thumbnails = snippet.get("thumbnails", {})
            if not isinstance(thumbnails, dict):
                continue

            medium = thumbnails.get("medium", {})
            if not isinstance(medium, dict):
                continue

            songs.append({
                "id": song_id,
                "title": snippet.get("title", "Unknown"),
                "thumbnail": medium.get("url", "")
            })

        return songs[:6]

    except Exception as e:
        print(f"YouTube API Error: {e}")
        # Fallback Mock Data organized by emotion if API fails or key is missing
        fallbacks = {
            "Sad": [
                {"id": "4N3N1MlvVc4", "title": "Mad World - Tearjerker Vibes", "thumbnail": "https://i.ytimg.com/vi/4N3N1MlvVc4/mqdefault.jpg"},
                {"id": "RgKAFK5djSk", "title": "See You Again (Emotional)", "thumbnail": "https://i.ytimg.com/vi/RgKAFK5djSk/mqdefault.jpg"},
                {"id": "hLQl3WQQoQ0", "title": "Someone Like You", "thumbnail": "https://i.ytimg.com/vi/hLQl3WQQoQ0/mqdefault.jpg"}
            ],
            "Happy": [
                {"id": "y6Sxv-sUYtM", "title": "Happy - Pharrell Williams", "thumbnail": "https://i.ytimg.com/vi/y6Sxv-sUYtM/mqdefault.jpg"},
                {"id": "ru0K8uYEZWw", "title": "CAN'T STOP THE FEELING!", "thumbnail": "https://i.ytimg.com/vi/ru0K8uYEZWw/mqdefault.jpg"}
            ],
            "Angry": [
                {"id": "aDaOpuYOie4", "title": "Linkin Park - Numb (Intense)", "thumbnail": "https://i.ytimg.com/vi/aDaOpuYOie4/mqdefault.jpg"},
                {"id": "1w7OgIMMRc4", "title": "Hard Rock / Metal Vibes", "thumbnail": "https://i.ytimg.com/vi/1w7OgIMMRc4/mqdefault.jpg"}
            ]
        }
        
        # Default to neutral chill beats if emotion not found
        default = [
            {"id": "5qap5aO4i9A", "title": "Lofi Hip Hop Radio - Chill Beats", "thumbnail": "https://i.ytimg.com/vi/5qap5aO4i9A/mqdefault.jpg"},
            {"id": "fLexgOxsZu0", "title": "The Lazy Song (Relaxed Tone)", "thumbnail": "https://i.ytimg.com/vi/fLexgOxsZu0/mqdefault.jpg"}
        ]
        
        return fallbacks.get(emotion, default)


def track_interaction(
    user_id: str, song_id: str, song_title: str, action: str
) -> None:
    """
    Records user interactions (play, skip, favorite) in Supabase.
    """
    try:
        supabase.table('interactions').insert({
            "user_id": user_id,
            "song_id": song_id,
            "song_title": song_title,
            "action": action
        }).execute()
    except Exception as e:
        print(f"Supabase Interaction Track Error: {e}")
