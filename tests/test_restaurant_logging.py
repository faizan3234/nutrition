from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_restaurant_without_verified_values_requires_opt_in():
    r=client.post('/api/restaurants/log',json={'profile':'abc1234rest','brand':'Arsalan','dish':'Chicken Biryani','grams':100,'meal':'Lunch'})
    assert r.status_code==422

def test_estimated_restaurant_logs_keep_provenance():
    data={'profile':'abc1234rest','brand':'Arsalan','dish':'Chicken Biryani','grams':300,'meal':'Lunch','use_generic_estimate':True}
    r=client.post('/api/restaurants/log',json=data);assert r.status_code==201,r.text
    j=r.json();assert j['restaurant_specific_nutrition'] is False
    assert 'illustrative_generic_recipe' in j['source']
    day=client.get('/api/day',params={'profile':data['profile'],'date':j['created_at'][:10]}).json()
    assert any(x['id']==j['id'] and 'Arsalan' in x['food_name'] for x in day['items'])
    assert client.delete('/api/log/'+j['id']+'?profile='+data['profile']).status_code==200
