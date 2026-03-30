# AI Emotion-Aware Music Recommendation System

This project uses Facial Emotion Recognition (AI) to curate music playlists from YouTube based on your mood.

## 🛠️ How to clear the "Red Lines" in your Editor

If you see red lines in your code editor, follow these steps:

### 1. Install Python Dependencies
The red lines in `app.py`, `emotion.py`, and `recommender.py` are because the libraries are not yet installed in your Python environment.
```bash
pip install -r requirements.txt
```

### 2. Fix Template Highlighting (VS Code)
The red lines in `.html` files occur because the editor thinks they are plain HTML, but they use **Jinja2** (the templating engine for Flask).
- Install the **"Jinja"** extension by *Don Jayamanne* or *wholroyd*.
- Alternatively, I've added a `.vscode/settings.json` file that tells VS Code to treat these as Jinja-HTML automatically.

### 3. Set your YouTube API Key
Open `models/recommender.py` and replace:
`YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"`
with your actual key from the Google Cloud Console.

## 🚀 Running the App
1. Open terminal in this folder.
2. Run `python init_db.py` (already done, but good to know).
3. Run `python app.py`.
4. Open `http://127.0.0.1:5000`.

## 🧪 Requirements
- Webcam access (for emotion detection).
- Internet connection (for YouTube API).
- Python 3.8+.
