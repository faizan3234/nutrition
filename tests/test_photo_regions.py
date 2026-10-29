import base64
import io
from unittest.mock import patch
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.photo_regions import PhotoRegion, analyze_regions
from app.vision import analyze, infer_onnx


def picture():
    im = Image.new('RGB', (200, 100), 'red')
    im.paste('blue', (100, 0, 200, 100))
    out = io.BytesIO(); im.save(out, format='PNG')
    return base64.b64encode(out.getvalue()).decode()


def test_individual_crops_discard_unmeasured_mass():
    seen = []
    def predict(encoded):
        im = Image.open(io.BytesIO(base64.b64decode(encoded)))
        seen.append((im.size, im.getpixel((50, 50))))
        return {'status': 'estimated', 'items': [{'grams': 300, 'min_grams': 200, 'max_grams': 400}]}
    regions = [PhotoRegion(x1=0,y1=0,x2=.5,y2=1), PhotoRegion(x1=.5,y1=0,x2=1,y2=1)]
    with patch('app.photo_regions.analyze', side_effect=predict):
        result = analyze_regions(picture(), regions)
    assert seen[0][0] == (100,100)
    assert seen[0][1][0] > 240 and seen[1][1][2] > 240
    assert [i['region'] for i in result['items']] == [1,2]
    assert all(i['grams'] is None and not i['mass_is_measured'] for i in result['items'])


@pytest.mark.parametrize('box', [dict(x1=.8,y1=0,x2=.2,y2=1), dict(x1=0,y1=0,x2=.001,y2=1), dict(x1=-1,y1=0,x2=1,y2=1)])
def test_invalid_regions_rejected(box):
    response = TestClient(app).post('/api/analyze', json={'image_base64':picture(),'regions':[box]})
    assert response.status_code == 422


def test_limit_and_empty_model():
    region = dict(x1=0,y1=0,x2=1,y2=1)
    client = TestClient(app)
    assert client.post('/api/analyze',json={'image_base64':picture(),'regions':[region]*7}).status_code == 422
    with patch('app.photo_regions.analyze', return_value={'status':'requires_model','items':[]}):
        data = client.post('/api/analyze',json={'image_base64':picture(),'regions':[region]}).json()
    assert data['regions'][0]['status'] == 'requires_model'
    assert data['items'] == []


def test_ambiguous_food_not_silently_mapped(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER','yolo')
    with patch('app.legacy_adapters.infer_yolo',return_value=[{'name':'unknown chicken cream dish','bbox':[0,0,1,1]}]):
        item = analyze(picture())['items'][0]
    assert item['food'] is None and item['requires_match']
    assert item['bbox'] == [0,0,1,1]


def test_classifier_runner_up_not_an_extra_dish():
    np = pytest.importorskip("numpy")
    class Session:
        def get_inputs(self):
            return [type('Input',(),{'name':'image'})()]
        def run(self,*args):
            return [np.array([[2.,1.8,0.]])]
    with patch('app.vision.get_onnx_session',return_value=(Session(),{0:'rice',1:'biryani',2:'pasta'})):
        items = infer_onnx(base64.b64decode(picture()))
    assert len(items) == 1
    assert items[0]['alternatives'] == ['biryani','pasta']


def test_failed_region_keeps_other_results():
    region = PhotoRegion(x1=0,y1=0,x2=1,y2=1)
    with patch('app.photo_regions.analyze',side_effect=[RuntimeError('private detail'), {'status':'estimated','items':[{'grams':20}]}]):
        data = analyze_regions(picture(),[region,region])
    assert data['regions'][0]['status'] == 'unavailable'
    assert len(data['items']) == 1
    assert 'private detail' not in str(data)
