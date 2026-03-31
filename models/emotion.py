import base64
from typing import List, Union, Dict, Any

import cv2  # type: ignore
import numpy as np  # type: ignore
from deepface import DeepFace  # type: ignore


def detect_emotion(image_data: str) -> str:
    """
    Detects emotion from a base64 encoded image string using DeepFace.
    Returns the dominant emotion capitalized (e.g., 'Happy', 'Sad', 'Neutral').
    If any error occurs during decoding or detection, it gracefully falls back
    to returning 'Neutral'.

    Args:
        image_data (str): A base64 string containing the image data.
                          Typically prefixed with 'data:image/jpeg;base64,'.

    Returns:
        str: The detected dominant emotion.
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

        # Analyze emotion directly bypassing secondary localized detectors (face is strictly pre-cropped in JS)
        results: Union[List[Dict[str, Any]], Dict[str, Any]] = (
            DeepFace.analyze(img, actions=['emotion'], detector_backend='skip', enforce_detection=False)
        )

        # Handle different DeepFace return signatures
        if isinstance(results, list):
            dominant = results[0].get('dominant_emotion', 'neutral')
        else:
            dominant = results.get('dominant_emotion', 'neutral')

        return str(dominant).capitalize()

    except ValueError as ve:
        # Expected error when a face genuinely isn't found
        print(f"DeepFace face detection error: {ve}")
        return "No face found"
    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return "Neutral"  # Fallback
