import json
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.packaged import normalize_product, scaled_product, lookup_barcode, search_products
from app.catalog import search_foods, FOODS

client=TestClient(app)

COLA={
 'code':'5449000000996','product_name':'Coca-Cola Original Taste','brands':'Coca-Cola',
 'quantity':'330 ml','product_quantity_unit':'ml',
 'nutriments':{'energy-kcal_100g':42,'proteins_100g':0,'carbohydrates_100g':10.6,'fat_100g':0}
}
SHAKE={
 'code':'8901234567890','product_name':'High Protein Drink Vanilla','brands':'Epigamia',
 'quantity':'200 ml','product_quantity_unit':'ml',
 'nutriments':{'energy-kcal_100g':80,'proteins_100g':10,'carbohydrates_100g':5,'fat_100g':2}
}

def test_colas_100_vs_300ml_scale():
    result=normalize_product(COLA)
    assert result['unit']=='ml'
    assert result['nutrition_basis']=='per 100 ml'
    assert scaled_product(result,100)=={'kcal':42,'protein':0,'carbs':10.6,'fat':0}
    assert scaled_product(result,300)=={'kcal':126,'protein':0,'carbs':31.8,'fat':0}


def test_epigamia_example_requires_exact_product_variant():
    result=normalize_product(SHAKE)
    assert 'Epigamia' in result['brand']
    assert scaled_product(result,100)['protein']==10
    assert scaled_product(result,300)['protein']==30
    assert result['source'].startswith('Open Food Facts')


def test_no_invented_variant_values():
    partial={**SHAKE,'nutriments':{'proteins_100g':10}}
    entry=normalize_product(partial)
    assert entry['complete'] is False
    assert sorted(entry['missing'])==['calories','carbohydrates','fat']
    with pytest.raises(ValueError):scaled_product(entry,200)


def test_zero_is_valid_missing_is_not_zero():
    entry=normalize_product(COLA)
    assert entry['fat']==0 and entry['complete'] is True
    assert normalize_product({**COLA,'nutriments':{'fat_100g':0}})['complete'] is False


def test_barcode_and_numeric_security():
    assert normalize_product({'code':'unsafe','product_name':'test','nutriments':{}}) is None
    for code in ('123','123<script>','abc','12345678901234567'):
        with pytest.raises(ValueError):lookup_barcode(code)
    bad={**COLA,'nutriments':{**COLA['nutriments'],'proteins_100g':'nan'}}
    assert normalize_product(bad)['complete'] is False


def test_logged_product_daily_and_unit(monkeypatch):
    monkeypatch.setattr('app.main.lookup_barcode',lambda _:normalize_product(SHAKE))
    saved=client.post('/api/products/log',json={
        'profile':'product-test-456','barcode':SHAKE['code'],'amount':300,'meal':'Snacks'})
    assert saved.status_code==201,saved.text
    row=saved.json()
    assert row['protein']==30 and row['unit']=='ml' and row['kcal']==240
    day=client.get('/api/day',params={'profile':'product-test-456','date':row['created_at'][:10]})
    assert day.status_code==200
    assert any(item['unit']=='ml' and item['protein']==30 for item in day.json()['items'])
    deleted=client.delete('/api/log/'+row['id']+'?profile=product-test-456')
    assert deleted.status_code==200


def test_product_api_missing_label_refused(monkeypatch):
    p=normalize_product({**SHAKE,'nutriments':{'proteins_100g':20}})
    monkeypatch.setattr('app.main.lookup_barcode',lambda _:p)
    res=client.post('/api/products/log',json={'profile':'product-test-456','barcode':SHAKE['code'],'amount':100,'meal':'Lunch'})
    assert res.status_code==422


def test_search_product_variants_no_hallucinated_brands(monkeypatch):
    monkeypatch.setattr('app.packaged._read',lambda url:{'products':[COLA,SHAKE,{'code':'junk','product_name':'fake'}]})
    items=search_products('Epigamia')
    assert len(items)==2
    assert items[0]['barcode']==COLA['code'] and items[1]['brand']=='Epigamia'


def test_barcode_api_mock(monkeypatch):
    monkeypatch.setattr('app.packaged._read',lambda url:{'product':COLA})
    lookup_barcode.cache_clear()
    res=client.get('/api/products/barcode/5449000000996')
    assert res.status_code==200
    assert res.json()['name']=='Coca-Cola Original Taste'
    lookup_barcode.cache_clear()


def test_generic_coverage_sausage_dal_drink_pasta():
    assert len(FOODS)>=190
    for q in ('chicken sausage','dal rice','pasta','coca cola','aloo','pizza','masala dosa','fish curry'):
        assert search_foods(q),q
