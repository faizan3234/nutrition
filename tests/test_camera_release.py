import base64
import io
import json
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.catalog import find_food
from app.vision import analyze, selected_provider, match_food_exact, model_info

client = TestClient(app)


def image_b64():
    image = Image.new('RGB', (96, 96), (220, 120, 60))
    b = io.BytesIO()
    image.save(b, format='JPEG')
    return base64.b64encode(b.getvalue()).decode('ascii')


def test_model_status_safe_without_weights(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER', 'auto')
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.setenv('ONNX_MODEL', 'models/nonexistent.onnx')
    monkeypatch.setenv('YOLO_WEIGHTS', 'models/nonexistent.pt')
    monkeypatch.setenv('NUTRILENS_WEIGHTS', 'models/nonexistent.h5')
    assert selected_provider() == 'none'
    x = client.get('/api/model-info').json()
    assert x['ready'] is False
    assert x['measured_recognition_accuracy_percent'] is None
    assert x['measured_weight_mae_grams'] is None


def test_exact_matching_doesnt_invent_food():
    assert match_food_exact('masala dosa')['id'] == 'masala-dosa'
    assert match_food_exact('chapati')['id'] == 'roti'
    assert match_food_exact('ambiguous unknown chickpea soup') is None
    assert match_food_exact('paneer') and match_food_exact('pasta') is None


def test_coverage_is_not_accuracy():
    c = client.get('/api/coverage').json()
    assert c['searchable_foods'] >= 170
    assert len(c['indian_22_model_labels']) == 22
    assert c['recognition_accuracy_on_171'] is None
    assert 'South Indian' in c['by_category']


def test_plate_diameter_validation():
    reject = client.post('/api/analyze', json={'image_base64': image_b64(), 'plate_diameter_cm': 100})
    assert reject.status_code == 422


def test_no_fabricated_weight_when_closed_set_classifier_used(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER', 'nutrilens')
    with patch('app.legacy_adapters.infer_nutrilens', return_value=[{'name': 'idli', 'model_score': 0.95}]):
        result = analyze(image_b64())
    assert result['items'][0]['portion_method'] == 'default_serving'
    assert result['items'][0]['mass_is_measured'] is False
    assert result['items'][0]['confidence'] == 'low'


def test_yolo_local_detector_adapter(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER', 'yolo')
    mock_boxes = [
        {'name': 'masala dosa', 'model_score': 0.88},
        {'name': 'sambar', 'model_score': 0.75}
    ]
    with patch('app.legacy_adapters.infer_yolo', return_value=mock_boxes):
        result = analyze(image_b64())
    assert result['provider'] == 'yolo'
    assert len(result['items']) == 2
    assert result['items'][0]['food']['id'] == 'masala-dosa'
    assert result['items'][1]['food']['id'] == 'sambar'


def test_groq_product_search(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'test-groq-key')
    mock_response = {
        'brand': 'Epigamia',
        'product_name': 'High Protein Milkshake Chocolate',
        'query': 'epigamia protein milkshake',
        'unit': 'ml',
        'per_100': {'kcal': 86.0, 'protein': 7.2, 'carbs': 9.5, 'fat': 2.1},
        'serving_size': 250,
        'confidence': 'high',
        'source': 'Groq online nutrition label search',
        'notes': 'Verified 18g protein per 250ml pack',
        'needs_user_confirmation': True
    }
    with patch('app.groq_service.search_packaged_nutrition', return_value=mock_response):
        res = client.post('/api/groq/product-search', json={'query': 'epigamia protein milkshake'})
        assert res.status_code == 200
        data = res.json()
        assert data['brand'] == 'Epigamia'
        assert data['per_100']['protein'] == 7.2
        assert data['unit'] == 'ml'


def test_groq_whisper_transcription(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'test-groq-key')
    with patch('app.groq_service.transcribe_audio', return_value='Epigamia chocolate milkshake 250ml'):
        fake_audio_b64 = base64.b64encode(b'RIFFfake-audio-bytes-wav').decode('ascii')
        res = client.post('/api/groq/transcribe', json={'audio_base64': fake_audio_b64, 'filename': 'audio.wav'})
        assert res.status_code == 200
        assert res.json()['text'] == 'Epigamia chocolate milkshake 250ml'


def test_onnx_local_classifier_inference(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER', 'onnx')
    mock_detected = [
        {'name': 'samosa', 'confidence': 'high', 'model_score': 0.89, 'grams': None, 'min_grams': None, 'max_grams': None}
    ]
    with patch('app.vision.infer_onnx', return_value=mock_detected):
        result = analyze(image_b64())
        assert result['provider'] == 'onnx'
        assert len(result['items']) == 1
        item = result['items'][0]
        assert item['detected_name'] == 'samosa'
        assert item['food']['name'] == 'Samosa'
        assert item['food']['kcal'] == 265.0
        assert item['food']['protein'] == 5.0
        assert item['grams'] == 100


def test_analyze_endpoint_with_onnx_live(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER', 'auto')
    res = client.post('/api/analyze', json={'image_base64': image_b64()})
    assert res.status_code == 200
    data = res.json()
    assert data['provider'] == 'onnx'
    assert len(data['items']) >= 1
    assert data['items'][0]['food'] is not None

