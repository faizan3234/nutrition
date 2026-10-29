from datetime import datetime, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import connection, init_db
from app.catalog import load_authorized_csv
from app.vision import analyze
from test_photo_regions import picture

client = TestClient(app)
PROFILE = 'portion-provenance-test'

@pytest.fixture(autouse=True)
def cleanup():
    with connection() as c:c.execute('DELETE FROM meal_logs WHERE profile=?',(PROFILE,))
    yield
    with connection() as c:c.execute('DELETE FROM meal_logs WHERE profile=?',(PROFILE,))


def payload(**extra):
    return dict(profile=PROFILE,food_id='steamed-rice',grams=300,meal='Lunch',**extra)


def test_weighed_leftovers_and_provenance_survive_diary_reload():
    response=client.post('/api/log',json=payload(leftover_amount=125,quantity_basis='scale',unit='g'))
    assert response.status_code==201,response.text
    row=response.json()
    # Known per-100g source values: 130 kcal and 2.7g protein, NOT photo ground truth.
    assert (row['grams'],row['kcal'],row['protein'])==(175,227.5,4.7)
    day=client.get('/api/day',params={'profile':PROFILE,'date':row['created_at'][:10]}).json()
    saved=day['items'][0]
    assert saved['leftover_amount']==125 and saved['quantity_basis']=='scale'
    assert saved['nutrition_quality']['tier']=='illustrative'
    assert saved['nutrition_quality']['measurement_verified'] is False
    assert saved['nutrition_quality']['accuracy_validated'] is False


def test_mixed_plate_separate_consumed_amounts_and_totals():
    items=[{'food_id':'steamed-rice','grams':300,'leftover_amount':125,'quantity_basis':'scale','unit':'g','meal':'Lunch'},
           {'food_id':'chicken-curry','grams':200,'consumed_percent':75,'quantity_basis':'manual_estimate','unit':'g','meal':'Lunch'}]
    response=client.post('/api/log/batch',json={'profile':PROFILE,'items':items})
    assert response.status_code==201,response.text
    data=response.json()
    assert [r['grams'] for r in data['items']]==[175,150]
    assert data['totals']['protein']==30.2
    assert data['totals']['kcal']==490


@pytest.mark.parametrize('extra',[
    {'leftover_amount':300},{'leftover_amount':301},{'leftover_amount':-1},
    {'leftover_amount':100,'consumed_percent':50}, {'unit':'ml'},
    {'quantity_basis':'measuring_container'}, {'quantity_basis':'ai_measured'},
])
def test_invalid_consumption_fails_without_logging(extra):
    assert client.post('/api/log',json=payload(**extra)).status_code==422
    with connection() as c:assert c.execute('SELECT COUNT(*) FROM meal_logs WHERE profile=?',(PROFILE,)).fetchone()[0]==0


def test_batch_unit_failure_is_atomic():
    valid=payload(unit='g'); valid.pop('profile')
    invalid={**valid,'unit':'ml'}
    assert client.post('/api/log/batch',json={'profile':PROFILE,'items':[valid,invalid]}).status_code==422
    with connection() as c:assert c.execute('SELECT COUNT(*) FROM meal_logs WHERE profile=?',(PROFILE,)).fetchone()[0]==0


def test_liquid_scale_rejected_and_measured_volume_accepted():
    data={**payload(),'food_id':'milk-whole','unit':'ml','quantity_basis':'scale'}
    assert client.post('/api/log',json=data).status_code==422
    data.update(quantity_basis='measuring_container',leftover_amount=50)
    response=client.post('/api/log',json=data)
    assert response.status_code==201,response.text
    assert response.json()['grams']==250 and response.json()['unit']=='ml'


def test_legacy_clients_not_relabelled_as_measured():
    row=client.post('/api/log',json=payload()).json()
    assert row['quantity_basis']=='unspecified'
    assert row['nutrition_quality']['measured_weight'] is False
    init_db(); init_db() # migration remains idempotent with saved rows
    with connection() as c:assert c.execute('SELECT grams FROM meal_logs WHERE id=?',(row['id'],)).fetchone()[0]==300


@pytest.mark.parametrize('value',['NaN','Infinity','-Infinity'])
def test_nonfinite_imported_protein_rejected(tmp_path,value):
    p=tmp_path/'foods.csv'
    p.write_text('name,kcal,protein,carbs,fat,source\nInvalid test food,100,'+value+',20,2,user\n')
    with pytest.raises(ValueError):load_authorized_csv(str(p))


def test_uncertain_classification_requires_food_selection(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER','onnx')
    with patch('app.vision.infer_onnx',return_value=[{'name':'steamed rice','requires_choice':True,'alternatives':['biryani chicken']} ]):
        result=analyze(picture())
    item=result['items'][0]
    assert item['food'] is None and item['requires_match']
    assert item['recognition_reason']=='uncertain_classifier'
    assert {f['id'] for f in item['candidates']}=={'steamed-rice','biryani-chicken'}


def test_upgrade_old_database_preserves_prior_logs(tmp_path,monkeypatch):
    import sqlite3
    from app import db
    path=tmp_path/'old.sqlite'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE meal_logs(id TEXT PRIMARY KEY,profile TEXT,food_id TEXT,food_name TEXT,grams REAL,meal TEXT,kcal REAL,protein REAL,carbs REAL,fat REAL,created_at TEXT)')
        c.execute("INSERT INTO meal_logs VALUES ('old','old-profile','rice','Rice',100,'Lunch',130,2.7,28,.3,'2026-10-29T00:00:00+00:00')")
    monkeypatch.setattr(db,'DB_PATH',str(path))
    db.init_db()
    with db.connection() as c:row=dict(c.execute("SELECT * FROM meal_logs WHERE id='old'").fetchone())
    assert row['protein']==2.7 and row['quantity_basis']=='unspecified'
    assert row['leftover_amount'] is None


def test_photo_mass_not_relabelled_as_drink_volume(monkeypatch):
    monkeypatch.setenv('VISION_PROVIDER','groq')
    with patch('app.vision.infer_groq_vision',return_value=[{'name':'milk whole','grams':417,'min_grams':300,'max_grams':500}]):
        result=analyze(picture())
    item=result['items'][0]
    assert item['unit']=='ml' and item['portion_method']=='default_serving'
    assert item['grams']!=417 and item['min_grams'] is None and item['max_grams'] is None
    assert item['food']['nutrition_quality']['tier']=='illustrative'
