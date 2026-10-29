"""Groq service integration for online packaged food label lookup and Whisper voice transcription.

Zero Gemini dependency. Uses Groq's high-speed inference for:
1. Online packaged food nutrition label search (e.g., Epigamia protein milkshakes, Amul Kool, etc.)
2. Speech/voice transcription via Groq Whisper API for hands-free meal and product search.
"""
from __future__ import annotations
import base64
import json
import os
import re
import urllib.request
import urllib.error

def get_groq_api_key() -> str:
    return os.getenv('GROQ_API_KEY', '').strip()

def search_packaged_nutrition(query: str) -> dict:
    """Search online manufacturer and retail nutrition labels for packaged foods using Groq."""
    key = get_groq_api_key()
    if not key:
        raise RuntimeError('Groq API key not configured. Set GROQ_API_KEY in your .env file to enable online label search.')

    clean_query = query.strip()
    if len(clean_query) < 2 or len(clean_query) > 150:
        raise ValueError('Product query must be between 2 and 150 characters')

    model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b').strip()
    # Sanitize model name
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', model):
        model = 'openai/gpt-oss-120b'

    system_prompt = (
        "You are an expert food nutrition search assistant for Indian and global packaged foods and drinks "
        "(such as Epigamia protein milkshake, Amul Kool, Raw Pressery, Yakult, packaged snacks, and beverages). "
        "Your task is to identify the exact verified or official printed nutrition label values from online product packaging. "
        "Always normalize values to PER 100g or PER 100ml. "
        "You MUST respond ONLY with a single JSON object containing exact numerical values. "
        "Do NOT invent numbers; if a nutrient is unknown or ambiguous, provide best conservative estimate based on standard FDA/FSSAI norms."
    )

    user_prompt = f"""Search online and find the printed packaging nutrition label information for:
"{clean_query}"

Return a valid JSON object strictly with this structure:
{{
  "brand": "Brand name (e.g., Epigamia, Amul)",
  "product_name": "Full product name and variant (e.g., High Protein Milkshake Chocolate)",
  "unit": "ml" or "g",
  "per_100": {{
    "kcal": <number calories per 100g or 100ml>,
    "protein": <number grams protein per 100g or 100ml>,
    "carbs": <number grams carbs per 100g or 100ml>,
    "fat": <number grams fat per 100g or 100ml>
  }},
  "serving_size": <typical package net quantity number or null>,
  "confidence": "high" or "medium" or "low",
  "source": "Groq online nutrition label search",
  "notes": "Short summary of verified product facts, e.g. 18g protein per 250ml pack"
}}"""

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "RelivNutritionAI/0.6.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status != 200:
                raise RuntimeError(f"Groq API returned status {res.status}")
            payload = json.load(res)
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode('utf-8', errors='ignore')
        # Fallback to qwen/qwen3.8-27b if needed
        if model != "qwen/qwen3.8-27b" and exc.code in (400, 404):
            body["model"] = "qwen/qwen3.8-27b"
            fallback_req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": "RelivNutritionAI/0.6.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(fallback_req, timeout=30) as res2:
                payload = json.load(res2)
        else:
            raise RuntimeError(f"Groq API error ({exc.code}): {err_msg[:200]}") from exc
    except Exception as exc:
        raise RuntimeError(f"Could not reach Groq API: {str(exc)}") from exc

    raw_text = payload.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        data = json.loads(raw_text)
    except Exception as exc:
        raise ValueError(f"Invalid JSON returned from Groq: {raw_text[:100]}") from exc

    per_100 = data.get("per_100") or {}
    for k in ("kcal", "protein", "carbs", "fat"):
        val = per_100.get(k)
        if val is None or not isinstance(val, (int, float)) or val < 0:
            raise ValueError(f"Incomplete nutrition figures for {k}")
        per_100[k] = round(float(val), 2)

    unit = str(data.get("unit") or "g").lower()
    if unit not in ("g", "ml"):
        unit = "ml" if "shake" in clean_query.lower() or "milk" in clean_query.lower() or "drink" in clean_query.lower() or "kool" in clean_query.lower() else "g"

    brand = str(data.get("brand") or "").strip()[:80]
    product_name = str(data.get("product_name") or clean_query).strip()[:140]
    serving_size = data.get("serving_size")
    if serving_size is not None:
        try:
            serving_size = float(serving_size)
        except (ValueError, TypeError):
            serving_size = None

    return {
        "brand": brand,
        "product_name": product_name,
        "query": clean_query,
        "unit": unit,
        "per_100": per_100,
        "serving_size": serving_size,
        "confidence": str(data.get("confidence") or "medium"),
        "source": "Groq online nutrition label search",
        "notes": str(data.get("notes") or ""),
        "needs_user_confirmation": True
    }

def transcribe_audio(audio_bytes: bytes, filename: str = "voice_input.webm") -> str:
    """Transcribe speech audio to text using Groq's high-speed Whisper model."""
    key = get_groq_api_key()
    if not key:
        raise RuntimeError('Groq API key not configured. Set GROQ_API_KEY in your .env file to enable voice transcription.')

    whisper_model = os.getenv('GROQ_WHISPER_MODEL', 'whisper-large-v3-turbo').strip()

    boundary = f"----WebKitFormBoundary{os.urandom(16).hex()}"
    body = bytearray()

    # Part 1: model
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
    body.extend(f"{whisper_model}\r\n".encode())

    # Part 2: file
    content_type = "audio/webm"
    if filename.endswith(".wav"):
        content_type = "audio/wav"
    elif filename.endswith(".mp3"):
        content_type = "audio/mpeg"
    elif filename.endswith(".m4a"):
        content_type = "audio/m4a"
    elif filename.endswith(".ogg"):
        content_type = "audio/ogg"

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(audio_bytes)
    body.extend(b"\r\n")

    # Part 3: response_format
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="response_format"\r\n\r\n')
    body.extend(b"json\r\n")

    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "RelivNutritionAI/0.6.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status != 200:
                raise RuntimeError(f"Groq Whisper returned status {res.status}")
            data = json.load(res)
            return str(data.get("text") or "").strip()
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f"Groq Whisper error ({exc.code}): {err_msg[:200]}") from exc
    except Exception as exc:
        raise RuntimeError(f"Voice transcription failed: {str(exc)}") from exc
