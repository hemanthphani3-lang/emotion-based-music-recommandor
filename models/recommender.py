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
            videoEmbeddable="true"
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
        # Fallback Mock Data if API fails or key is missing
        return [
            {
                "id": "dQw4w9WgXcQ",
                "title": f"Fallback: Upbeat {emotion} Tracks",
                "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg"
            },
            {
                "id": "3JZ_D3i301s",
                "title": f"Soulful {emotion} Vibes",
                "thumbnail": "https://i.ytimg.com/vi/3JZ_D3i301s/mqdefault.jpg"
            }
        ]


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
