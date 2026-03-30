import cv2
import numpy as np
from deepface import DeepFace
import base64
import os

def detect_emotion(image_data):
    """
    Detects emotion from base64 image data.
    """
    try:
        if not image_data:
            return "Neutral"
            
        # Decode base64
        header, encoded = image_data.split(",", 1)
        data = base64.b64decode(encoded)
        
        # Convert to numpy array
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Analyze emotion
        # Note: DeepFace.analyze can be slow on first run as it downloads weights
        results = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
        
        if isinstance(results, list):
            return results[0]['dominant_emotion'].capitalize()
        return results['dominant_emotion'].capitalize()
        
    except Exception as e:
        print(f"Error in emotion detection: {e}")
        return "Neutral" # Fallback
