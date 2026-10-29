"""Camera food recognition with conservative provenance and portion handling.

Supports:
1. Groq Vision (llama-3.2-11b-vision-preview): fast multimodal recognition for Indian & global meals.
2. Local YOLO multi-food detector (models/food_detector.pt).
3. Local NutriLens classifier (models/nutrilens.h5).
4. Local CLIP zero-shot classifier.
5. Admin-approved reference match.

Zero Gemini dependencies.
"""
from __future__ import annotations
import base64
import io
import json
import os
import re
import urllib.request
from PIL import Image, ImageOps
from .catalog import LOOKUP, search_foods

MAX_IMAGE_BYTES = 7_000_000


def normalize_image(image_b64: str) -> bytes:
    if ',' in image_b64:
        image_b64 = image_b64.split(',', 1)[1]
    if len(image_b64) > MAX_IMAGE_BYTES * 1.5:
        raise ValueError('Image too large')
    try:
        raw = base64.b64decode(image_b64, validate=True)
    except Exception as exc:
        raise ValueError('Invalid image encoding') from exc
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError('Image too large')
    try:
        im = Image.open(io.BytesIO(raw))
        if im.format not in ('PNG', 'JPEG', 'WEBP'):
            raise ValueError('Use JPEG, PNG or WEBP')
        im = ImageOps.exif_transpose(im)
        if im.width * im.height > 18_000_000:
            raise ValueError('Image dimensions too large')
        im = im.convert('RGB')
        im.thumbnail((1440, 1440))
        dst = io.BytesIO()
        im.save(dst, format='JPEG', quality=82, optimize=True)
        return dst.getvalue()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('Image cannot be decoded') from exc


_onnx_session = None
_onnx_labels = None


def get_onnx_session():
    global _onnx_session, _onnx_labels
    if _onnx_session is None:
        try:
            import onnxruntime as ort
        except ImportError:
            return None, None
        model_path = os.getenv('ONNX_MODEL', 'models/food_classifier.onnx')
        labels_path = os.getenv('ONNX_LABELS', 'models/food_labels.json')
        if not os.path.isfile(model_path) or not os.path.isfile(labels_path):
            return None, None
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _onnx_session = ort.InferenceSession(model_path, opts, providers=['CPUExecutionProvider'])
        with open(labels_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            _onnx_labels = {int(k): v.replace('_', ' ') for k, v in raw.items()}
    return _onnx_session, _onnx_labels


def infer_onnx(image: bytes) -> list[dict]:
    session, labels = get_onnx_session()
    if session is None or labels is None:
        raise RuntimeError('Local ONNX food classifier model or labels not found')
    import numpy as np

    im = Image.open(io.BytesIO(image)).convert('RGB')
    im = im.resize((224, 224), Image.Resampling.BILINEAR)
    arr = np.array(im, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = arr.transpose(2, 0, 1)
    arr = np.expand_dims(arr, axis=0)

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: arr})
    logits = outputs[0][0]

    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / np.sum(exp_logits)
    top_indices = np.argsort(probs)[::-1]

    top_idx = int(top_indices[0])
    top_score = float(probs[top_idx])
    label_name = labels.get(top_idx, 'unknown')
    conf = 'high' if top_score > 0.3 else ('medium' if top_score > 0.1 else 'low')

    items = [{
        'name': label_name,
        'grams': None,
        'min_grams': None,
        'max_grams': None,
        'confidence': conf,
        'model_score': round(top_score, 4)
    }]

    second_idx = int(top_indices[1])
    second_score = float(probs[second_idx])
    if second_score > 0.15:
        items.append({
            'name': labels.get(second_idx, 'unknown'),
            'grams': None,
            'min_grams': None,
            'max_grams': None,
            'confidence': 'medium',
            'model_score': round(second_score, 4)
        })

    return items


def selected_provider() -> str:
    """Select the active vision provider.

    In 'auto' mode, priority is:
    YOLO detector -> Local ONNX Food Classifier -> NutriLens classifier -> Groq Vision (if key configured) -> CLIP -> none.
    """
    provider = os.getenv('VISION_PROVIDER', 'auto').strip().lower()
    if provider == 'auto':
        from pathlib import Path
        from importlib.util import find_spec
        yolo_path = Path(os.getenv('YOLO_WEIGHTS', 'models/food_detector.pt'))
        if yolo_path.is_file() and find_spec('ultralytics') is not None:
            return 'yolo'
        onnx_model = Path(os.getenv('ONNX_MODEL', 'models/food_classifier.onnx'))
        onnx_labels = Path(os.getenv('ONNX_LABELS', 'models/food_labels.json'))
        if onnx_model.is_file() and onnx_labels.is_file() and find_spec('onnxruntime') is not None:
            return 'onnx'
        nutri_w = Path(os.getenv('NUTRILENS_WEIGHTS', 'models/nutrilens.h5'))
        nutri_l = Path(os.getenv('NUTRILENS_LABELS', 'models/nutrilens_labels.json'))
        if nutri_w.is_file() and nutri_l.is_file() and find_spec('tensorflow') is not None:
            return 'nutrilens'
        if os.getenv('VISION_PROVIDER') == 'groq' and os.getenv('GROQ_API_KEY', '').strip():
            return 'groq'
        if find_spec('transformers') is not None:
            return 'clip'
        return 'none'
    return provider


def model_info() -> dict:
    from pathlib import Path
    from importlib.util import find_spec
    provider = selected_provider()
    requirements = {
        'none': (False, 'No vision provider configured. Set your free GROQ_API_KEY in .env or add local model weights.'),
        'onnx': (
            Path(os.getenv('ONNX_MODEL', 'models/food_classifier.onnx')).is_file() and
            Path(os.getenv('ONNX_LABELS', 'models/food_labels.json')).is_file() and
            find_spec('onnxruntime') is not None,
            'Local Food-101 Swin Transformer (ONNX CPU)'
        ),
        'groq': (bool(os.getenv('GROQ_API_KEY', '').strip()), 'Requires GROQ_API_KEY in .env (get free key at console.groq.com)'),
        'clip': (find_spec('transformers') is not None, 'Requires transformers and downloaded model'),
        'nutrilens': (
            Path(os.getenv('NUTRILENS_WEIGHTS', 'models/nutrilens.h5')).is_file() and
            Path(os.getenv('NUTRILENS_LABELS', 'models/nutrilens_labels.json')).is_file() and
            find_spec('tensorflow') is not None,
            'Requires authorized H5 model, labels.json and TensorFlow'
        ),
        'yolo': (
            Path(os.getenv('YOLO_WEIGHTS', 'models/food_detector.pt')).is_file() and
            find_spec('ultralytics') is not None,
            'Requires authorized YOLO weights and Ultralytics'
        ),
    }
    ready, requirement = requirements.get(provider, (False, 'Unknown provider'))
    return {
        'provider': provider,
        'ready': ready,
        'requirements': requirement,
        'live_inference_verified': False,
        'model': (
            'Food-101 Swin Transformer (ONNX)' if provider == 'onnx' else
            (os.getenv('GROQ_VISION_MODEL', 'llama-3.2-11b-vision-preview') if provider == 'groq' else provider)
        ),
        'measured_recognition_accuracy_percent': None,
        'measured_weight_mae_grams': None,
        'measured_calorie_mae_kcal': None,
        'measured_protein_mae_grams': None,
        'recognition_scope': (
            '101_food_categories_local_onnx' if provider == 'onnx' else
            ('open_vocabulary_multimodal' if provider == 'groq' else
             ('22_categories_only' if provider == 'nutrilens' else
              ('multi_food_detection' if provider == 'yolo' else 'provider_dependent')))
        ),
        'portion_scope': (
            'visual_estimate_with_ranges_not_measured' if provider == 'groq' else 'user_supplied_grams_required'
        ),
        'nutrition_data_quality': 'illustrative_until_source_verified',
        'warning': 'No independent camera/portion/calorie/protein benchmark for this combined project.'
    }


def infer_groq_vision(images: list[bytes], plate_diameter_cm: float | None) -> list[dict]:
    """Recognize Indian and international foods using Groq multimodal vision."""
    key = os.getenv('GROQ_API_KEY', '').strip()
    if not key:
        raise RuntimeError('Groq API key not configured. Set GROQ_API_KEY in .env to enable camera recognition.')

    model = os.getenv('GROQ_VISION_MODEL', 'llama-3.2-11b-vision-preview').strip()
    plate_text = f"Known plate diameter: {plate_diameter_cm:g} cm." if plate_diameter_cm else "No plate size specified."

    prompt = f"""You are analyzing a photographed meal for an Indian and international nutrition diary.
Recognize EACH distinct visible edible food or dish item (e.g. Masala Dosa, Idli, Sambar, Coconut Chutney,
Biryani, Steamed Rice, Dal Tadka, Paneer Butter Masala, Roti, Naan, Chicken Curry, Salad, Fruit, Pizza, etc.).
{plate_text}
Estimate approximate edible cooked mass in grams for each visible food.
Respond STRICTLY with a single JSON object in this format:
{{"items": [{{"name": "Masala Dosa", "grams": 180, "min_grams": 140, "max_grams": 240, "confidence": "high", "note": "crispy dosa with potato filling"}}]}}
At most 10 items. Output valid JSON only, no markdown formatting."""

    content_parts = [{"type": "text", "text": prompt}]
    for im in images:
        b64_img = base64.b64encode(im).decode('ascii')
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
        })

    body = {
        "model": model,
        "messages": [{"role": "user", "content": content_parts}],
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
        with urllib.request.urlopen(req, timeout=35) as res:
            if res.status != 200:
                raise RuntimeError(f"Groq Vision returned status {res.status}")
            data = json.load(res)
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f"Groq Vision API error ({exc.code}): {err_msg[:200]}") from exc
    except Exception as exc:
        raise RuntimeError(f"Groq Vision request failed: {str(exc)}") from exc

    raw_text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        obj = json.loads(raw_text)
        return obj.get("items", []) if isinstance(obj, dict) else []
    except Exception:
        return []


def infer_clip(image: bytes):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError('Install optional model dependencies (requirements-vision.txt)') from exc
    from functools import lru_cache

    @lru_cache(maxsize=1)
    def get_pipeline():
        return pipeline(
            task='zero-shot-image-classification',
            model=os.getenv('CLIP_MODEL', 'openai/clip-vit-base-patch32')
        )

    im = Image.open(io.BytesIO(image))
    candidates = [f['name'] for f in search_foods('', 500)]
    outputs = get_pipeline()(im, candidate_labels=candidates)
    return [{
        'name': outputs[0]['label'],
        'grams': None,
        'min_grams': None,
        'max_grams': None,
        'confidence': 'low',
        'model_score': float(outputs[0]['score'])
    }]


def match_food_exact(label: str):
    """Exact slug or alias match in catalog."""
    key = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
    if key in LOOKUP:
        return LOOKUP[key]
    for food in LOOKUP.values():
        for alias in food['aliases']:
            if key == re.sub(r'[^a-z0-9]+', '-', alias.lower()).strip('-'):
                return food
    return None


def match_food_flexible(label: str):
    """Match label using exact match first, then keyword search against catalog."""
    exact = match_food_exact(label)
    if exact:
        return exact

    # Try search_foods for partial and token matching
    candidates = search_foods(label, 5)
    if candidates:
        l_tokens = set(re.findall(r'[a-z0-9]+', label.lower()))
        for c in candidates:
            c_tokens = set(re.findall(r'[a-z0-9]+', c['name'].lower()))
            if l_tokens & c_tokens:
                return c
        return candidates[0]
    return None


def _weight(value):
    if value is None:
        return None
    try:
        number = float(value)
        if not 1 <= number <= 5000:
            return None
        return round(number)
    except (TypeError, ValueError, OverflowError):
        return None


def analyze(image_b64: str, secondary_image_b64: str | None = None,
            plate_diameter_cm: float | None = None):
    images = [normalize_image(image_b64)]
    if secondary_image_b64:
        images.append(normalize_image(secondary_image_b64))

    from .learning import compare_photo
    reference = compare_photo(images[0])
    if reference['match_type'] == 'exact_photo':
        return {
            'provider': 'admin_reference',
            'status': 'reference_exact',
            'items': reference['items'],
            'reference_candidates': [],
            'message': 'Matches an admin-reviewed example photo. Confirm food, recipe, and eaten quantity.'
        }

    provider = selected_provider()
    if provider == 'onnx':
        raw_items = infer_onnx(images[0])
    elif provider == 'groq':
        raw_items = infer_groq_vision(images, plate_diameter_cm)
    elif provider == 'clip':
        raw_items = infer_clip(images[0])
    elif provider in ('nutrilens', 'yolo'):
        from .legacy_adapters import infer_nutrilens, infer_yolo
        raw_items = infer_nutrilens(images[0]) if provider == 'nutrilens' else infer_yolo(images[0])
    else:
        return {
            'provider': 'none',
            'status': 'requires_model',
            'items': [],
            'reference_candidates': reference['candidates'],
            'message': 'No vision model is active. Add your free GROQ_API_KEY in .env to activate instant AI camera scanning, or use food search below.'
        }

    result = []
    for obj in raw_items[:12]:
        if not isinstance(obj, dict):
            continue
        label = str(obj.get('name', ''))[:100].strip()
        food = match_food_flexible(label) if label and label.lower() != 'unknown' else None
        if not food:
            result.append({
                'detected_name': label or 'unknown',
                'food': None,
                'requires_match': True,
                'grams': None,
                'confidence': 'low',
                'needs_confirmation': True
            })
            continue

        grams = _weight(obj.get('grams'))
        low = _weight(obj.get('min_grams'))
        high = _weight(obj.get('max_grams'))
        if low is not None and high is not None and low > high:
            low, high = high, low
        if grams is not None and (low is None or high is None):
            low, high = round(grams * 0.5), round(grams * 1.5)

        result.append({
            'detected_name': label,
            'food': food,
            'requires_match': False,
            'grams': grams if grams is not None else food['default_grams'],
            'min_grams': low,
            'max_grams': high,
            'confidence': str(obj.get('confidence', 'low')),
            'model_score': obj.get('model_score'),
            'portion_method': 'uncalibrated_photo_estimate' if grams is not None else 'default_serving',
            'mass_is_measured': False,
            'needs_confirmation': True,
            'nutrition_source': food['source'],
        })

    return {
        'provider': provider,
        'status': 'estimated',
        'items': result,
        'reference_candidates': reference['candidates'],
        'message': (
            'Estimated, NOT weighed. Verify each dish and grams before logging. ' +
            ('A second angle and plate size may reduce uncertainty.' if len(images) == 1 else
             'Two photos were captured, but food weight is still an estimate.')
        )
    }
