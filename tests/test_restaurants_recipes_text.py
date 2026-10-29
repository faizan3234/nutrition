from fastapi.testclient import TestClient
from app.main import app
from app.catalog import LOOKUP
from app.restaurants import search_restaurants, estimate_restaurant
from app.textlog import parse_entry
from app.recipes import calculate_recipe
from decimal import Decimal

client=TestClient(app)

def test_official_menu_not_calories():
    rows=search_restaurants('Arsalan');assert len(rows)>3
    assert rows[0]['nutrition'] is None
    assert all(x['verified_menu_item'] and not x['nutrition_verified_for_specific_dish'] for x in rows)
    assert client.get('/api/restaurants?q=Arsalan').status_code==200

def test_restaurant_requires_opt_in():
    j=client.post('/api/restaurants/estimate',json={'brand':'Arsalan','dish':'Chicken Biryani','grams':300}).json()
    assert j['nutrition'] is None and j['requires_explicit_generic_opt_in']
    j=client.post('/api/restaurants/estimate',json={'brand':'Arsalan','dish':'Chicken Biryani','grams':300,'use_generic_estimate':True}).json()
    assert j['source']=='illustrative_generic_recipe' and j['nutrition']['kcal']>0
    assert j['is_restaurant_specific'] is False

def test_unknown_restaurant_no_fabricated_data():
    assert client.post('/api/restaurants/estimate',json={'brand':'Kareem’s','dish':'Chicken Biryani','grams':250}).status_code==404

def test_package_weight_not_edible_weight():
    item=search_restaurants('Biryani By Kilo')[0]
    assert item['advertised_pack_weight_g']==500
    assert item['nutrition'] is None

def test_restaurant_authorized_csv(tmp_path,monkeypatch):
    file=tmp_path/'verified.csv'
    file.write_text('brand,dish,kcal_100g,protein_100g,carbs_100g,fat_100g,evidence_url,verified_on,reviewer\nArsalan,Chicken Biryani,200,13,20,7,https://example.com/test-proof,2026-10-29,QA-team\n')
    monkeypatch.setenv('RELIV_RESTAURANT_NUTRITION_CSV',str(file))
    j=estimate_restaurant('Arsalan','Chicken Biryani',300)
    assert j['source']=='audited_restaurant_nutrition' and j['nutrition']['protein']==39


def test_text_brand_no_fake_sku():
    for t in ('I had Coca Cola 300ml','Epigamia 100ml protein shake','Arsalan chicken biryani 300g'):
        r=parse_entry(t)
        assert r['kind']=='branded_product_or_restaurant' and not r['auto_logged']

def test_text_weight_rice_and_dal():
    r=parse_entry('I had 100g rice')
    assert r['kind']=='generic_food' and r['grams']==100
    assert r['nutrition']['kcal']==LOOKUP['steamed-rice']['kcal']
    r=parse_entry('I had 300 g dal chawal')
    assert r['kind']=='generic_food' and r['grams']==300

def test_text_ambiguous_food_no_first_match():
    r=parse_entry('100g pizza')
    assert r['kind']=='ambiguous' and len(r['candidates'])>=2 and not r['auto_logged']

def test_mixed_meal_requires_confirmation():
    res=client.post('/api/parse-meal',json={'text':'100g rice, 200g dal tadka and Epigamia 100ml'})
    assert res.status_code==200
    j=res.json();assert len(j['items'])==3
    assert j['ready_to_log']==False and j['items'][2]['kind']=='branded_product_or_restaurant'

def test_recipe_oil_ghee_ingredient_conservation():
    # illustration only: arithmetic preserves sum and applies cooked yield.
    items=[{'food_id':'steamed-rice','grams':100},{'food_id':'dal-tadka','grams':200},
           {'name':'Cooking oil','grams':10,'per100':{'kcal':900,'protein':0,'carbs':0,'fat':100},'source_note':'User-provided label'}]
    r=calculate_recipe(items,300)
    assert r['total']['kcal']>90
    assert r['per_100g_cooked']['kcal']==float((Decimal(str(r['total']['kcal']))/3).quantize(Decimal('.1')) ) or abs(r['per_100g_cooked']['kcal']-r['total']['kcal']/3)<=.1
    assert r['nutrition_verified'] is False

def test_recipe_requires_source_for_custom_ingredient():
    res=client.post('/api/recipes/estimate',json={'ingredients':[{'grams':100,'name':'secret'}]})
    assert res.status_code==422


def test_readiness_honest():
    j=client.get('/api/readiness').json()
    assert j['production_ready'] is False and 'real_image_detection_map' in j['blocking_gates']

def test_idli_piece_count_is_only_estimated():
    r=parse_entry('I ate 2 idli')
    assert r['kind']=='generic_food'
    assert r['quantity_method']=='typical_piece_assumption'
    assert r['grams']==2*r['food']['default_grams']
    assert r['auto_logged'] is False
