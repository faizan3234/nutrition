from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_mixed_plate_batch_logs_and_totals():
    profile='batch-test-001'
    items=[{'food_id':'dal-tadka','grams':100,'meal':'Lunch'},
           {'food_id':'steamed-rice','grams':300,'meal':'Lunch'},
           {'food_id':'aloo-sabzi','grams':100,'meal':'Lunch'},
           {'food_id':'sausage-chicken-cooked-generic','grams':100,'meal':'Lunch'}]
    res=client.post('/api/log/batch',json={'profile':profile,'items':items})
    assert res.status_code==201,res.text
    data=res.json()
    assert data['count']==4
    assert data['totals']['kcal']>400
    assert data['totals']['protein']>20
    for row in data['items']:
        assert row['unit']=='g'
        client.delete('/api/log/'+row['id'],params={'profile':profile})


def test_batch_is_atomic_if_one_unknown():
    profile='batch-test-002'
    test=client.post('/api/log/batch',json={'profile':profile,'items':[
        {'food_id':'roti','grams':100,'meal':'Lunch'},
        {'food_id':'unsupported','grams':300,'meal':'Lunch'}]})
    assert test.status_code==404


def test_batch_limit_protects_server():
    data={'profile':'batch-test-002','items':[{'food_id':'roti','grams':1,'meal':'Lunch'}]*13}
    assert client.post('/api/log/batch',json=data).status_code==422
