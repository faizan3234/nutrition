"""Real consumption and presentation must not be conflated.

These are API arithmetic tests, NOT real-photo portion estimation measurements.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.catalog import LOOKUP, nutrients
client=TestClient(app)

def _clean(profile, rows):
    for row in rows:
        res=client.delete(f"/api/log/{row['id']}",params={'profile':profile})
        assert res.status_code==200

def test_half_of_300g_logs_150g_not_300g():
    profile='consumption-half-01'
    r=client.post('/api/log',json={'profile':profile,'food_id':'steamed-rice', 'grams':300,
                                    'consumed_percent':50,'meal':'Lunch'})
    assert r.status_code==201,r.text
    entry=r.json()
    assert entry['served_amount']==300
    assert entry['grams']==150
    assert entry['consumed_percent']==50
    assert entry['protein']==nutrients(LOOKUP['steamed-rice'],150)['protein']
    data=client.get('/api/day',params={'profile':profile,'date':entry['created_at'][:10]}).json()
    stored=next(x for x in data['items'] if x['id']==entry['id'])
    assert stored['served_amount']==300 and stored['grams']==150
    assert stored['consumed_percent']==50
    _clean(profile,[entry])

def test_batch_tracks_different_consumption_for_each_plate_item():
    profile='consumption-mixed-01'
    req={'profile':profile,'items':[
      {'food_id':'steamed-rice','grams':300,'consumed_percent':25,'meal':'Dinner'},
      {'food_id':'dal-tadka','grams':200,'consumed_percent':75,'meal':'Dinner'},
      {'food_id':'aloo-sabzi','grams':100,'meal':'Dinner'}]}
    r=client.post('/api/log/batch',json=req)
    assert r.status_code==201,r.text
    out=r.json()
    assert [x['grams'] for x in out['items']]==[75,150,100]
    assert [x['served_amount'] for x in out['items']]==[300,200,100]
    assert [x['consumed_percent'] for x in out['items']]==[25,75,100]
    assert out['totals']['kcal']==round(sum(nutrients(LOOKUP[x['food_id']],x['grams'])['kcal'] for x in out['items']),1)
    _clean(profile,out['items'])

def test_invalid_consumed_ratios_rejected():
    for p in [0,-1,101,150]:
        response=client.post('/api/log',json={'profile':'consumption-bad-01', 'food_id':'roti','grams':100,
                                              'consumed_percent':p,'meal':'Lunch'})
        assert response.status_code==422,(p,response.text)

def test_legacy_clients_default_to_all_eaten():
    profile='consumption-legacy-01'
    resp=client.post('/api/log',json={'profile':profile, 'food_id':'steamed-rice',
                                      'grams':100,'meal':'Lunch'})
    assert resp.status_code==201,resp.text
    row=resp.json()
    assert row['grams']==row['served_amount']==100
    assert row['consumed_percent']==100
    _clean(profile,[row])
