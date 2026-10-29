"""Software tests only; do NOT interpret as empirical macro/vision accuracy."""
from fastapi.testclient import TestClient
from app.catalog import FOODS, LOOKUP, nutrients, serving_unit, search_foods
from app.main import app
from app.textlog import parse_entry, parse_meal_text

client=TestClient(app)

def test_catalog_has_requested_food_families():
    assert len(FOODS)>=280
    required=("Sizzling Brownie With Ice Cream","New York Cheesecake","Falooda",
              "Tiramisu","Virgin Mojito Sugared","Virgin Mojito No Sugar",
              "Fried Rice Chicken","Fried Rice Prawn","Fried Rice Schezwan Veg",
              "Kolkata Chicken Biryani","Cold Coffee With Ice Cream","Sausage Chicken Cooked Generic")
    for name in required:
        assert any(food['name']==name for food in FOODS),name
    assert len([f for f in FOODS if f['category']=='Desserts']) >= 30
    assert len([f for f in FOODS if f['category']=='Mocktails']) >= 15

def test_mocktail_volume_is_in_millilitres_not_grams():
    for f in FOODS:
        if f['category']=='Mocktails':assert serving_unit(f)=='ml'
    assert serving_unit(LOOKUP['fried-rice-chicken'])=='g'
    result=parse_entry('300ml virgin mojito sugared')
    assert result['kind']=='generic_food'
    assert result['grams']==300
    assert result['unit']=='ml'
    api=client.post('/api/log',json={'profile':'mocktail-user-123','food_id':'virgin-mojito-sugared', 'grams':300,'meal':'Snacks'})
    assert api.status_code==201,api.text
    assert api.json()['unit']=='ml'
    deleted=client.delete('/api/log/'+api.json()['id'],params={'profile':'mocktail-user-123'})
    assert deleted.status_code==200

def test_100_300_ml_and_gram_math():
    for food in [LOOKUP['virgin-mojito-sugared'], LOOKUP['chocolate-brownie'], LOOKUP['fried-rice-chicken']]:
        a=nutrients(food,100);b=nutrients(food,300)
        for k in ['kcal','protein','carbs','fat']:
            assert abs(b[k] - 3*a[k])<=0.11,(food['name'],k)

def test_low_sugar_is_not_interchangeable_with_sugared():
    a=LOOKUP['virgin-mojito-sugared'];b=LOOKUP['virgin-mojito-no-sugar']
    assert nutrients(a,300)['kcal']>nutrients(b,300)['kcal']
    assert parse_entry('virgin mojito')['kind']=='ambiguous'

def test_broad_names_demand_variety_selection():
    for text in ('fried rice','cheesecake','mocktail','mojito','pasta','pizza','smoothie'):
        result=parse_entry(text)
        assert result['kind']=='ambiguous',(text,result['kind'])
        assert not result['auto_logged']

def test_specific_food_suggestions_and_mixed_meal():
    assert search_foods('chicken fried rice')[0]['name']=='Fried Rice Chicken'
    r=parse_meal_text('200g chicken fried rice and 120g sizzling brownie and 300ml virgin mojito no sugar')
    assert len(r['items'])==3
    assert [it['kind'] for it in r['items']]==['generic_food']*3
    assert [it['unit'] for it in r['items']]==['g','g','ml']
    assert r['requires_review']

def test_updated_coverage_api_does_not_claim_photo_accuracy():
    j=client.get('/api/coverage').json()
    assert j['searchable_foods']==len(FOODS)
    assert j['recognition_accuracy_catalog'] is None
    assert j['portion_accuracy_catalog'] is None
    assert 'Mocktails' in j['by_category']
