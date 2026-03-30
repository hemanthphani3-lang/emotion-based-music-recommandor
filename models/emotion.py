import base64
from typing import List, Union, Dict, Any

import cv2  # type: ignore
import numpy as np  # type: ignore
from deepface import DeepFace  # type: ignore


def detect_emotion(image_data: str) -> str:
    """
    Detects emotion from base64 image data using DeepFace.
    Returns the dominant emotion (e.g., 'Happy', 'Sad', 'Neutral').
    """
    try:
        if not image_data or "," not in image_data:
            return "Neutral"

        # Decode base64 header and data
        _, encoded = image_data.split(",", 1)
        data = base64.b64decode(encoded)

        # Convert to numpy array for OpenCV
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return "Neutral"

        # Analyze emotion
        # Note: DeepFace.analyze can be slow on first run (models download)
        results: Union[List[Dict[str, Any]], Dict[str, Any]] = (
            DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
        )

        # Handle different DeepFace return signatures
        if isinstance(results, list):
            dominant = results[0].get('dominant_emotion', 'neutral')
        else:
            dominant = results.get('dominant_emotion', 'neutral')

        return str(dominant).capitalize()

    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return "Neutral"  # Fallback
