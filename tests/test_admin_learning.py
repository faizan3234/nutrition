"""Regression tests for reviewed-learning data, not real-world AI accuracy."""
import base64
import io
import os
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app import db, learning
from app.vision import normalize_image

TOKEN='learning-admin-secret-that-is-over-32-characters-long'
client=TestClient(app)

@pytest.fixture
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',str(tmp_path/'test.sqlite'))
    monkeypatch.setattr(learning,'DATA_DIR',tmp_path/'private')
    monkeypatch.setenv('RELIV_ADMIN_TOKEN',TOKEN)
    monkeypatch.setenv('RELIV_ENV','local')
    monkeypatch.setenv('VISION_PROVIDER','none')
    db.init_db();learning.initialize()
    yield tmp_path

@pytest.fixture
def image():
    im=Image.new('RGB',(256,170),'#fff4dd')
    draw=ImageDraw.Draw(im);draw.ellipse((15,10,230,155),fill='#c9d0d6');draw.ellipse((30,26,128,124),fill='#da9b35');draw.ellipse((137,30,218,127),fill='#895836')
    b=io.BytesIO();im.save(b,format='JPEG',quality=85)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()

@pytest.fixture
def items():
    return [
     {'name':'Biryani', 'recipe_variant':'home cooked with 10g oil','grams':100,'kcal':180,'protein':7,'carbs':25,'fat':6,
      'source_kind':'weighed_recipe','evidence_url':'','note':'Cooked batch with weighed ingredients','bbox':[.1,.12,.5,.75]},
     {'name':'Dal tadka','recipe_variant':'home dal tadka','grams':300,'kcal':110,'protein':6,'carbs':16,'fat':3,
      'source_kind':'weighed_recipe','evidence_url':'','note':'Full recipe weighed, cooked yield recorded','bbox':[.51,.1,.9,.8]},
    ]

def auth():return {'Authorization':'Bearer '+TOKEN}

def post(image,items):
    return client.post('/api/admin/learning/examples',headers=auth(),json={
        'image_base64':image,'photo_group':'kitchen-1-session-2026','photo_use_rights_confirmed':True,'items':items})

def test_admin_is_disabled_without_config(isolated,monkeypatch):
    monkeypatch.setenv('RELIV_ADMIN_TOKEN','')
    assert client.get('/api/admin/learning/stats').status_code==503
    monkeypatch.setenv('RELIV_ADMIN_TOKEN',TOKEN)
    assert client.get('/api/admin/learning/stats').status_code==401
    assert client.get('/api/admin/learning/stats',headers={'Authorization':'Bearer badtoken'}).status_code==401
    assert client.get('/api/admin/learning/stats',headers=auth()).status_code==200

def test_separate_admin_website_exists(isolated):
    assert client.get('/admin').status_code==200
    assert 'Admin Learning Studio' in client.get('/admin').text
    assert client.get('/admin/assets/app.js').status_code==200
    assert 'reliv' in client.get('/').text.lower()

def test_training_examples_require_approval(isolated,image,items):
    res=post(image,items)
    assert res.status_code==201,res.text
    assert res.json()['status']=='pending_review'
    assert len(res.json()['example_ids'])==2
    assert client.get('/api/admin/learning/examples',headers=auth()).json()['items'][0]['status']=='pending'
    photo=client.post('/api/analyze',json={'image_base64':image})
    assert photo.status_code==200
    assert photo.json()['items']==[]
    assert photo.json()['status']=='requires_model'
    assert len(list((isolated/'private').glob('*.jpg')))==1
    # The private photo itself is not served from public assets.
    assert client.get('/assets/'+list((isolated/'private').glob('*.jpg'))[0].name).status_code==404

def test_multi_item_exact_reference_and_confirmed_logging(isolated,image,items):
    j=post(image,items).json()
    for sid in j['example_ids']:
        assert client.post(f'/api/admin/learning/examples/{sid}/approved',headers=auth()).status_code==200
    scanned=client.post('/api/analyze',json={'image_base64':image}).json()
    assert scanned['status']=='reference_exact'
    assert sorted(x['grams'] for x in scanned['items'])==[100,300]
    assert all(x['mass_is_measured'] is False and x['needs_confirmation'] for x in scanned['items'])
    ids=[x['food']['id'] for x in scanned['items']]
    logged=client.post('/api/log/batch',json={'profile':'food-profile-1234','items':[
        {'food_id':ids[0],'grams':300,'meal':'Lunch'},{'food_id':ids[1],'grams':100,'meal':'Lunch'}]})
    assert logged.status_code==201,logged.text
    assert logged.json()['count']==2
    # Both food quantities are scaled separately, not fixed to reference grams.
    assert {x['food_name'] for x in logged.json()['items']}=={'Biryani','Dal tadka'}
    assert {x['grams'] for x in logged.json()['items']}=={100.0,300.0}
    assert all(x['source'].startswith('admin_reviewed:') for x in logged.json()['items'])

def test_similar_image_never_inherits_portion(isolated,image,items):
    j=post(image,items).json()
    for sid in j['example_ids']:
        client.post(f'/api/admin/learning/examples/{sid}/approved',headers=auth())
    raw=normalize_image(image)
    im=Image.open(io.BytesIO(raw))
    b=io.BytesIO();im.save(b,format='JPEG',quality=44)
    changed=base64.b64encode(b.getvalue()).decode()
    assert normalize_image(changed)!=raw
    result=client.post('/api/analyze',json={'image_base64':changed}).json()
    assert result['status']=='requires_model'
    assert result['items']==[]
    assert result['reference_candidates']
    assert all(x['grams'] is None for x in result['reference_candidates'])
    assert all('NOT verified same food' in x['warning'] for x in result['reference_candidates'])

def test_rejected_never_suggested(isolated,image,items):
    ids=post(image,items).json()['example_ids']
    for sid in ids:
        client.post(f'/api/admin/learning/examples/{sid}/rejected',headers=auth())
    assert not client.post('/api/analyze',json={'image_base64':image}).json()['items']
    assert not client.get('/api/admin/learning/export',headers=auth()).json()['items']
    assert client.post(f'/api/admin/learning/examples/{ids[0]}/approved',headers=auth()).status_code==422

def test_validation_rejects_bad_bbox_or_amount(isolated,image,items):
    bad=[{**items[0], 'bbox':[0.5,0.6,0.1,0.9]}]
    assert post(image,bad).status_code==422
    bad=[{**items[0], 'grams':0}]
    assert post(image,bad).status_code==422
    bad=[{**items[0], 'protein':120}]
    assert post(image,bad).status_code==422
    assert client.post('/api/admin/learning/examples',headers=auth(),json={'image_base64':image,'photo_group':'a','photo_use_rights_confirmed':True,'items':items}).status_code==422

def test_training_manifest_split_and_acl(isolated,image,items):
    ids=post(image,items).json()['example_ids']
    client.post(f'/api/admin/learning/examples/{ids[0]}/approved',headers=auth())
    assert client.get('/api/admin/learning/export').status_code==401
    manifest=client.get('/api/admin/learning/export',headers=auth()).json()['items']
    assert len(manifest)==1
    assert manifest[0]['bbox']==items[0]['bbox']
    assert manifest[0]['dataset_split']==learning.group_split('kitchen-1-session-2026')
    assert learning.group_split('kitchen-1-session-2026')==learning.group_split('kitchen-1-session-2026')

def test_feedback_opt_in_and_no_auto_promotion(isolated,image,items):
    payload={'profile':'feedback-person-123','corrected_name':'Chicken biryani','corrected_grams':300,
             'comment':'This is not veg biryani','consent_to_admin_review':False}
    assert client.post('/api/learning/feedback',json=payload).status_code==422
    payload['consent_to_admin_review']=True
    payload['image_base64']=image
    response=client.post('/api/learning/feedback',json=payload)
    assert response.status_code==201,response.text
    fid=response.json()['feedback_id']
    assert client.get('/api/admin/learning/feedback').status_code==401
    queue=client.get('/api/admin/learning/feedback',headers=auth()).json()['items']
    assert len(queue)==1
    assert 'profile' not in queue[0] and 'image_path' not in queue[0]
    assert client.post(f'/api/admin/learning/feedback/{fid}/approved',headers=auth()).status_code==200
    assert client.get('/api/admin/learning/export',headers=auth()).json()['items']==[]
    assert client.post('/api/analyze',json={'image_base64':image}).json()['items']==[]

def test_admin_stats_never_fabricate_model_accuracy(isolated,image,items):
    post(image,items)
    stats=client.get('/api/admin/learning/stats',headers=auth()).json()
    assert stats['samples']['pending']==2
    assert stats['real_photo_recognition_accuracy'] is None
    assert stats['food_detection_map50'] is None
    assert stats['portion_weight_mae_g'] is None

def test_nutrition_basis_total_portion_normalizes_to_per100(isolated,image,items):
    recorded={**items[0], 'grams':300, 'nutrient_basis':'total_for_weighed_portion',
              'kcal':540,'protein':21,'carbs':75,'fat':18}
    j=post(image,[recorded])
    assert j.status_code==201,j.text
    sid=j.json()['example_ids'][0]
    assert client.post(f'/api/admin/learning/examples/{sid}/approved',headers=auth()).status_code==200
    result=client.post('/api/analyze',json={'image_base64':image}).json()
    food=result['items'][0]['food']
    assert food['kcal']==180
    assert food['protein']==7
    assert food['carbs']==25
    assert food['fat']==6
    assert result['items'][0]['grams']==300
    # 100g and 300g must calculate differently even when reference was 300g.
    a=client.post('/api/log',json={'profile':'profile-total-grams','food_id':food['id'],'grams':100,'meal':'Lunch'})
    b=client.post('/api/log',json={'profile':'profile-total-grams','food_id':food['id'],'grams':300,'meal':'Lunch'})
    assert a.status_code==b.status_code==201
    assert a.json()['kcal']==180 and b.json()['kcal']==540
    assert a.json()['protein']==7 and b.json()['protein']==21


def test_missing_macros_require_input_not_silent_zero(isolated,image,items):
    bad=[{**items[0], 'protein':None}]
    assert post(image,bad).status_code==422

def test_validation_dashboard_is_protected_and_does_not_claim_metrics(isolated):
    assert client.get('/api/admin/learning/validation').status_code==401
    response=client.get('/api/admin/learning/validation',headers=auth())
    assert response.status_code==200
    body=response.json()
    assert body['production_ready'] is False
    assert len(body['gates'])>=20
    for gate in body['gates']:
        assert gate['metric'] is None
    assert {g['id'] for g in body['gates']}>={'mAP50','grams_mae','100_vs_300','protein_mae'}


def test_uploaded_photo_rights_must_be_attested(isolated,image,items):
    response=client.post('/api/admin/learning/examples',headers=auth(),json={
        'image_base64':image,'photo_group':'rights-check-1','items':items,
        'photo_use_rights_confirmed':False})
    assert response.status_code==422
    assert 'photo' in response.json()['detail'].lower()


def test_admin_can_revoke_incorrect_reference_without_breaking_diary(isolated, image, items):
    ident = post(image, [items[0]]).json()['example_ids'][0]
    assert client.post(f'/api/admin/learning/examples/{ident}/approved', headers=auth()).status_code == 200
    ref = client.post('/api/analyze',json={'image_base64':image}).json()['items'][0]['food']['id']
    logged = client.post('/api/log',json={'profile':'history-person-124','food_id':ref,'grams':250,'meal':'Dinner'})
    assert logged.status_code == 201
    path=f'/api/admin/learning/examples/{ident}/revoke'
    assert client.post(path,json={'reason':'Food label was wrong'}).status_code == 401
    assert client.post(path,headers=auth(),json={'reason':'bad'}).status_code == 422
    revoked=client.post(path,headers=auth(),json={'reason':'Wrong dish and recipe, needs new verified sample'})
    assert revoked.status_code == 200
    assert revoked.json()['status'] == 'revoked'
    assert client.post('/api/analyze',json={'image_base64':image}).json()['items'] == []
    assert client.get('/api/admin/learning/examples?status=revoked',headers=auth()).json()['items'][0]['id']==ident
    assert client.get('/api/admin/learning/export',headers=auth()).json()['items']==[]
    assert client.post('/api/log',json={'profile':'history-person-124','food_id':ref,'grams':100,'meal':'Dinner'}).status_code==404
    history=client.get('/api/day?profile=history-person-124&date='+logged.json()['created_at'][:10]).json()
    assert any(x['id']==logged.json()['id'] for x in history['items'])
    assert client.post(path,headers=auth(),json={'reason':'This is a duplicate revocation'}).status_code==422


def test_feedback_photo_admin_preview_and_separate_training_consent(isolated,image):
    payload={'profile':'someone-12345','corrected_name':'Chicken biryani','corrected_grams':300,
            'comment':'Homemade version with 1 tbsp oil','consent_to_admin_review':True,
            'image_base64':image}
    recorded=client.post('/api/learning/feedback',json=payload)
    assert recorded.status_code==201,recorded.text
    fid=recorded.json()['feedback_id']
    correction=client.get('/api/admin/learning/feedback',headers=auth()).json()['items'][0]
    assert correction['has_image'] is True and correction['training_consent'] is False
    path=f'/api/admin/learning/feedback/{fid}/photo'
    assert client.get(path).status_code==401
    read=client.get(path,headers=auth())
    assert read.status_code==200 and read.headers['content-type']=='image/jpeg'
    assert read.headers['cache-control']=='no-store'
    assert read.content.startswith(b'\xff\xd8')
    assert 'image_path' not in correction and 'profile' not in correction
    assert client.get('/api/admin/learning/feedback/not-a-valid-id/photo',headers=auth()).status_code==404

    payload['consent_to_reference_training']=True
    allowed=client.post('/api/learning/feedback',json=payload)
    assert allowed.status_code==201
    all_feedback=client.get('/api/admin/learning/feedback',headers=auth()).json()['items']
    assert any(x['training_consent'] is True for x in all_feedback)
    payload.pop('image_base64')
    assert client.post('/api/learning/feedback',json=payload).status_code==422
    # Admin reviewed feedback does NOT directly alter recognition or models.
    assert client.get('/api/admin/learning/export',headers=auth()).json()['items']==[]
    assert client.post('/api/analyze',json={'image_base64':image}).json()['items']==[]
