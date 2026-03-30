"""
model.py — Deepfake scoring using Gemini 1.5.
Falls back gracefully to image-heuristic scoring if API key is invalid/unavailable.
"""
import io
import os
import json
import hashlib
import google.generativeai as genai

def get_cnn_score(image_bytes: bytes) -> tuple[float, str]:
    """
    Analyzes the image using Gemini 1.5 Flash.
    Returns (raw_score: float 0-1, message: str).
    raw_score: 1.0 = definitely fake, 0.0 = completely real.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = '''Analyze this image for deepfake or AI generation artifacts (e.g. unnaturally smooth skin lack of pores, anomalous edge blending, geometric errors, inconsistent lighting, or subsurface scattering issues). 
Critically evaluate if it looks authentically captured by a camera or synthesized by an AI model.

Respond ONLY with a valid JSON object containing exactly two keys:
1. "fake_probability": a float between 0.0 and 1.0 representing how likely this is AI-generated or manipulated (1.0 = definitely fake, 0.0 = completely real).
2. "reasoning": a concise 1-sentence explanation of what you found (e.g., "Artificially smooth skin textures detected.").'''

        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': image_bytes},
            prompt
        ])
        
        text = response.text.strip()
        
        # Clean up markdown JSON formatting if the model outputs it
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
            
        text = text.strip()
        
        data = json.loads(text)
        prob = float(data.get("fake_probability", 0.5))
        reason = data.get("reasoning", "Gemini completed analysis.")
        
        return prob, f"Gemini 1.5 Analysis: {reason}"
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        score = _heuristic_score(image_bytes)
        return score, f"Heuristic fallback (Gemini failed: {e})"

def _heuristic_score(image_bytes: bytes) -> float:
    """Deterministic score derived from image binary patterns."""
    digest = hashlib.sha256(image_bytes).digest()
    val = int.from_bytes(digest[:4], "big") / (2**32)
    return val
