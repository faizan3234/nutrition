import base64
import io
import os
import tempfile
from pathlib import Path
from PIL import Image
os.environ['NUTRITION_DB_PATH']=str(Path(tempfile.gettempdir())/'reliv-test-nutrition.sqlite3')
os.environ['VISION_PROVIDER']='none'
from fastapi.testclient import TestClient
from app.main import app
from app.catalog import FOODS,nutrients,find_food,search_foods
client=TestClient(app)

def test_foods_broad():
    assert len(FOODS)>=155
    for food in ['Masala Dosa','Paneer Butter Masala','Pizza Margherita','Pasta White Sauce','Machher Jhol','Idli']:
        assert find_food(food),food
    assert search_foods('dosa')

def test_100_300_grams_protein_calories():
    f=find_food('Paneer Plain')
    a=nutrients(f,100);b=nutrients(f,300)
    assert b['protein']==3*a['protein']
    assert b['kcal']==3*a['kcal']
    assert b['protein']==54
    assert b['kcal']==795

def test_invalid_grams():
    import pytest
    with pytest.raises(ValueError):nutrients(find_food('Idli'),0)

def test_full_logging_cycle():
    prof='test-user-1234';f=find_food('Masala Dosa')
    r=client.post('/api/log',json={'profile':prof,'food_id':f['id'],'grams':300,'meal':'Breakfast'})
    assert r.status_code==201, r.text
    data=r.json();assert data['protein']==nutrients(f,300)['protein']
    date=data['created_at'][:10]
    read=client.get('/api/day',params={'profile':prof,'date':date})
    assert read.status_code==200 and read.json()['totals']['kcal']>=data['kcal']
    deleted=client.delete('/api/log/'+data['id'],params={'profile':prof})
    assert deleted.status_code==200

def test_image_requires_provider_and_validates_image():
    img=Image.new('RGB',(64,64),'orange');buf=io.BytesIO();img.save(buf,format='JPEG')
    image=base64.b64encode(buf.getvalue()).decode()
    r=client.post('/api/analyze',json={'image_base64':image})
    assert r.status_code==200 and r.json()['status']=='requires_model'
    bad=client.post('/api/analyze',json={'image_base64':'a'*1000})
    assert bad.status_code==400

def test_scanning_not_falsely_automatic():
    res=client.get('/api/health')
    assert res.status_code==200 and res.json()['status']=='prototype'
