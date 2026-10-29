from app.usda import normalize_fdc,search_usda
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

EXAMPLE={'fdcId':123456,'dataType':'Foundation','description':'Rice, white, cooked',
 'foodNutrients':[{'nutrientId':1008,'value':130},{'nutrientId':1003,'value':2.7},
                  {'nutrientId':1004,'value':0.3},{'nutrientId':1005,'value':28}]}

def test_usda_nutrient_ids():
    r=normalize_fdc(EXAMPLE)
    assert r['per_100g']['kcal']==130
    assert r['per_100g']['protein']==2.7 and r['category']=='Foundation'
    assert '123456' in r['source_url']

def test_usda_rejects_incomplete_or_branded():
    assert normalize_fdc({**EXAMPLE,'dataType':'Branded'}) is None
    assert normalize_fdc({**EXAMPLE,'foodNutrients':[{'nutrientId':1003,'value':10}]}) is None

def test_usda_endpoint_without_key_returns_honest_status(monkeypatch):
    monkeypatch.delenv('FDC_API_KEY',raising=False)
    r=client.get('/api/reference-foods?q=rice')
    assert r.status_code==503 and 'key not configured' in r.json()['detail']

def test_usda_mock_search(monkeypatch):
    from app import usda
    class Fake:
        def __enter__(self):return self
        def __exit__(self,*x):return False
        def read(self):return b'{"foods": []}'
    monkeypatch.setenv('FDC_API_KEY','example-secret')
    monkeypatch.setattr(usda.urllib.request,'urlopen',lambda req,timeout:Fake())
    assert search_usda('rice')==[]

def test_reference_food_logged_with_exact_fdc_and_provenance(monkeypatch):
    from app import main
    monkeypatch.setattr(main,'lookup_usda',lambda fdc_id:normalize_fdc(EXAMPLE))
    base={'profile':'nutrition-fdc-1234','fdc_id':123456,'grams':100,'meal':'Dinner'}
    a=client.post('/api/reference-foods/log',json=base)
    assert a.status_code==201,a.text
    j=a.json();assert j['protein']==2.7 and 'USDA' in j['source']
    b=client.post('/api/reference-foods/log',json={**base,'grams':300})
    assert b.status_code==201
    assert b.json()['protein']==8.1 and b.json()['kcal']==390
    client.delete('/api/log/'+j['id']+'?profile='+base['profile'])
    client.delete('/api/log/'+b.json()['id']+'?profile='+base['profile'])
