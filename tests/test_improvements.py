"""New convenience/provenance features; never a camera accuracy benchmark."""
import base64, io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.catalog import search_foods,LOOKUP
from app.quality import nutrition_quality
from app.recipes import calculate_recipe
from app.evaluation_monitor import summarize

c=TestClient(app)
PROFILE='improvement-user-2026'

def test_bengali_hindi_hinglish_food_names():
    assert search_foods('চাল')==[]
    assert search_foods('চावल')==[]
    assert search_foods('भात')==[]
    assert search_foods('চোলার ডাল')[0]['id']=='cholar-dal'
    assert search_foods('आलू दम')[0]['id']=='aloo-dum'
    assert search_foods('aloo posto')[0]['id']=='aloo-posto'
    assert search_foods('chawal')[0]['id']=='steamed-rice'
    assert search_foods('चावल')[0]['id']=='steamed-rice'
    assert len(search_foods('বিরিয়ানি'))>1
    assert any('veg' in x['name'].lower() for x in search_foods('বিরিয়ানি'))

def test_saved_plate_is_not_claimed_to_weigh_food():
    r=c.put('/api/me/plate',json={'profile':PROFILE,'diameter_cm':26,'label':'Home thali'})
    assert r.status_code==200 and 'does not measure grams' in r.json()['warning']
    q=c.get('/api/me/plate',params={'profile':PROFILE})
    assert q.json()['plate']['diameter_cm']==26
    assert c.put('/api/me/plate',json={'profile':PROFILE,'diameter_cm':90,'label':'invalid'}).status_code==422

def test_user_shortcuts_and_half_portion_are_profile_scoped():
    f=LOOKUP['dal-tadka']
    s=c.post('/api/me/shortcuts',json={'profile':PROFILE,'food_id':f['id'],
       'serving_amount':300,'nickname':'Usual dinner dal'})
    assert s.status_code==201,s.text
    sid=s.json()['id']
    assert any(x['id']==sid for x in c.get('/api/me/shortcuts',params={'profile':PROFILE}).json()['items'])
    assert c.post(f'/api/me/shortcuts/{sid}/log',json={'profile':'someone-else-profile','fraction':1,'meal':'Dinner'}).status_code==404
    x=c.post(f'/api/me/shortcuts/{sid}/log',json={'profile':PROFILE,'fraction':0.5,'meal':'Dinner'})
    assert x.status_code==201,x.text
    assert x.json()['grams']==150
    assert x.json()['nutrition_quality']['tier']=='illustrative'
    assert c.delete('/api/log/'+x.json()['id'],params={'profile':PROFILE}).status_code==200

def test_recipe_warns_of_hidden_fat_and_raw_cooked_mixture():
    ingredients=[{'food_id':'dal-tadka','grams':200,'role':'prepared_base','preparation':'cooked'},
      {'food_id':'ghee-generic','grams':20,'role':'added_fat','preparation':'raw'}]
    result=calculate_recipe(ingredients,None)
    assert len(result['safety_warnings'])==2
    assert 'oil' in result['safety_warnings'][0]
    assert result['ingredients'][0]['preparation']=='cooked'

def test_quality_is_honest():
    assert nutrition_quality('illustrative_starter_not_verified')['tier']=='illustrative'
    assert not nutrition_quality('USDA FoodData Central')['accuracy_validated']
    assert not nutrition_quality('weighed_recipe')['measured_weight']
    assert nutrition_quality('weighed_recipe','scale')['measured_weight']

def test_manual_label_100_300ml_and_review_required():
    payload={'profile':PROFILE,'brand':'Example','name':'Yogurt drink',
       'amount':300,'unit':'ml','per_100':{'kcal':60,'protein':9,'carbs':5,'fat':1},'meal':'Snacks'}
    assert c.post('/api/products/label/log',json=payload).status_code==422
    payload['label_verified_by_user']=True
    r=c.post('/api/products/label/log',json=payload)
    assert r.status_code==201,r.text
    assert r.json()['kcal']==180
    assert r.json()['protein']==27
    assert r.json()['nutrition_quality']['tier']=='user_label'
    assert c.delete('/api/log/'+r.json()['id'],params={'profile':PROFILE}).status_code==200
    payload['per_100'].pop('fat')
    assert c.post('/api/products/label/log',json=payload).status_code==422

def test_ocr_fails_closed_without_local_tesseract(monkeypatch):
    im=Image.new('RGB',(48,48),'white');out=io.BytesIO();im.save(out,format='JPEG')
    b64=base64.b64encode(out.getvalue()).decode()
    r=c.post('/api/products/label/read',json={'image_base64':b64})
    assert r.status_code==503

def test_heldout_evaluation_no_claim_on_fake_training_split():
    valid=[{'sample_id':'photoA','split':'test','true_label':'Dal Tadka','predicted_label':'Dal Tadka',
            'true_grams':100,'predicted_grams':300,'true_kcal':115,'predicted_kcal':345,
            'true_protein':6,'predicted_protein':18,'group':'Indian mixed plate'},
           {'sample_id':'photoB','split':'test','true_label':'Pizza','predicted_label':'Pasta',
            'true_grams':200,'predicted_grams':200,'true_kcal':300,'predicted_kcal':300,
            'true_protein':10,'predicted_protein':10,'group':'fast foods'}]
    x=summarize(valid)
    assert x['metrics']['top1_recognition_accuracy_percent']==50
    assert x['metrics']['grams_mae']==100
    assert x['sample_count']==2
    assert 'detection_mAP50' in x['not_measured']
    for rows in ([dict(valid[0],split='train')],[valid[0],valid[0]]):
        import pytest
        with pytest.raises(ValueError):summarize(rows)

def test_admin_triage_auth_and_benchmark_auth(monkeypatch):
    monkeypatch.setenv('RELIV_ADMIN_TOKEN','M'*40)
    assert c.get('/api/admin/learning/triage').status_code==401
    assert c.post('/api/admin/evaluate/heldout',json={'rows':[]}).status_code in (401,422)
    r=c.get('/api/admin/learning/triage',headers={'Authorization':'Bearer '+'M'*40})
    assert r.status_code==200
    assert 'frequent_corrections' in r.json()
