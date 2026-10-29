"""Opt-in package nutrition panel transcription using local OCR, requiring user confirmation.

Zero cloud vision / zero Gemini dependency.
Uses local Tesseract OCR when installed; otherwise fails closed and instructs the user
to enter the printed label numbers manually.
"""
from __future__ import annotations
import io
import re
import shutil
from PIL import Image
from .vision import normalize_image

def _parse_label_text(text: str) -> dict:
    """Extract standard nutrition facts from OCR text."""
    lines = text.lower().splitlines()
    
    # Check unit
    unit = 'ml' if re.search(r'\b(ml|millilitre|milliliter)\b', text.lower()) else 'g'
    
    # Helper to find numbers following a nutrient keyword
    def find_num(patterns: list[str], max_val: float) -> float | None:
        for p in patterns:
            m = re.search(p + r'[:\s-]*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1))
                    if 0 <= val <= max_val:
                        return val
                except ValueError:
                    pass
        return None

    kcal = find_num([r'energy', r'calories', r'kcal'], 1000.0)
    protein = find_num([r'protein'], 100.0)
    carbs = find_num([r'carbohydrate', r'carbs', r'total carb'], 100.0)
    fat = find_num([r'total fat', r'fat'], 100.0)

    if None in (kcal, protein, carbs, fat):
        raise ValueError('Could not read all 4 required nutrients (kcal, protein, carbs, fat) from label image. Please enter them manually.')

    return {
        'brand': '',
        'name': 'Scanned package label',
        'unit': unit,
        'per_100': {
            'kcal': round(kcal, 1),
            'protein': round(protein, 1),
            'carbs': round(carbs, 1),
            'fat': round(fat, 1)
        },
        'needs_user_confirmation': True,
        'verified': False,
        'source': 'local_tesseract_ocr_unverified',
        'warning': 'Check calories, protein, carbs, fats, basis and serving unit against physical packaging.'
    }

def read_label(image_base64: str) -> dict:
    image_bytes = normalize_image(image_base64)
    
    # Check if local tesseract is installed
    has_tesseract_binary = shutil.which('tesseract') is not None
    try:
        import pytesseract
        has_pytesseract = True
    except ImportError:
        has_pytesseract = False

    if not (has_tesseract_binary and has_pytesseract):
        raise RuntimeError('Local Tesseract OCR is not installed or configured. Please enter the printed label figures manually in the form below.')

    try:
        image = Image.open(io.BytesIO(image_bytes))
        ocr_text = pytesseract.image_to_string(image)
        if not ocr_text or len(ocr_text.strip()) < 10:
            raise ValueError('Label text was illegible or blurry. Please enter figures manually.')
        return _parse_label_text(ocr_text)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f'Local OCR failed: {str(exc)}') from exc
