import base64
import io
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from app import db,learning
from training.portion_pairs import generate

@pytest.fixture
def dbdir(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',str(tmp_path/'portion.sqlite'))
    monkeypatch.setattr(learning,'DATA_DIR',tmp_path/'private')
    db.init_db();learning.initialize()
    return tmp_path

def photo(size):
    im=Image.new('RGB',(200,200),'white')
    ImageDraw.Draw(im).ellipse((30,30,30+size,30+size),fill='orange')
    out=io.BytesIO();im.save(out,format='JPEG')
    return base64.b64encode(out.getvalue()).decode()

def example(grams,weight_basis='scale'):
    return [{'name':'Biryani','recipe_variant':'same weighed kitchen recipe','grams':grams,
             'weight_basis':weight_basis,'nutrient_basis':'per_100g',
             'kcal':190,'protein':8,'carbs':25,'fat':7,
             'source_kind':'weighed_recipe','note':'Complete recipe weighed, including all cooking oil',
             'bbox':[.1,.1,.9,.9]}]

def test_scale_measured_pair_generation(dbdir):
    for amount,size in [(100,55),(300,140)]:
        e=learning.create_examples(photo(size),example(amount),'same-recipe-batch',plate_diameter_cm=26,rights_confirmed=True)
        learning.review_sample(e['example_ids'][0],'approved')
    report=generate(dbdir/'portion.sqlite',dbdir/'pairs.csv')
    assert report['mass_ratio_pairs']==1
    import csv
    row=list(csv.DictReader((dbdir/'pairs.csv').open()))[0]
    assert float(row['small_grams'])==100
    assert float(row['large_grams'])==300
    assert float(row['ratio'])==3
    assert float(row['small_plate_cm'])==26

def test_estimated_portion_cannot_be_used_as_ground_truth(dbdir):
    for amount,size in [(100,55),(300,140)]:
        e=learning.create_examples(photo(size),example(amount,'estimated'),'uncalibrated-pair',rights_confirmed=True)
        learning.review_sample(e['example_ids'][0],'approved')
    report=generate(dbdir/'portion.sqlite',dbdir/'none.csv')
    assert report['mass_ratio_pairs']==0
    assert report['scale_weighed_examples']==0
