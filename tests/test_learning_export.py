import base64
import io
from pathlib import Path
import pytest
from PIL import Image,ImageDraw
from app import db,learning
from training.export_curated import build_export
from scripts.evaluate_curated import evaluate

@pytest.fixture
def store(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',str(tmp_path/'data.sqlite'))
    monkeypatch.setattr(learning,'DATA_DIR',tmp_path/'private')
    db.init_db();learning.initialize()
    return tmp_path

def photo(color='#aa7333'):
    image=Image.new('RGB',(200,140),'#eee8df')
    ImageDraw.Draw(image).ellipse((5,5,170,120),fill=color)
    b=io.BytesIO();image.save(b,format='JPEG',quality=89)
    return base64.b64encode(b.getvalue()).decode()

def items():
    return [
      {'name':'Biryani','grams':100,'source_kind':'weighed_recipe','kcal':180,'protein':7,'carbs':25,'fat':6,'note':'Ingredients and cooked yield measured','bbox':[0.1,0.1,0.45,0.8]},
      {'name':'Dal tadka','grams':300,'source_kind':'weighed_recipe','kcal':110,'protein':6,'carbs':16,'fat':3,'note':'Recipe ingredient weights documented','bbox':[0.5,0.2,0.9,0.95]},
    ]

def test_export_contains_real_crops_boxes_and_grouped_splits(store):
    d=learning.create_examples(photo(),items(),'batch-kitchen-A',rights_confirmed=True)
    for id in d['example_ids']:learning.review_sample(id,'approved')
    result=build_export(store/'data.sqlite',store/'output')
    assert result['approved_examples']==2
    assert result['classification_crops']==2
    assert result['detection_images']==1
    assert result['detection_boxes']==2
    assert (store/'output'/'detector'/'data.yaml').exists()
    assert len(list((store/'output'/'detector'/'labels').rglob('*.txt')))==1
    assert len(list((store/'output'/'classification').rglob('*.jpg')))==2
    assert set(result['labels'])=={'biryani','dal-tadka'}
    assert result['note'].startswith('Curated training dataset')
    assert evaluate(store/'data.sqlite')['status']=='insufficient_data'

def test_export_rejects_same_photo_cross_split_leakage(store):
    names={}
    for i in range(100):
        group=f'session-{i}'
        names.setdefault(learning.group_split(group),group)
    assert len(names)>=2
    a,b=list(names.values())[:2]
    one=[items()[0]]
    d1=learning.create_examples(photo(),one,a,rights_confirmed=True)
    d2=learning.create_examples(photo(),one,b,rights_confirmed=True)
    for sid in d1['example_ids']+d2['example_ids']:
        learning.review_sample(sid,'approved')
    with pytest.raises(ValueError,match='different training and evaluation splits'):
        build_export(store/'data.sqlite',store/'output')

def test_export_excludes_pending_items_from_detection(store):
    d=learning.create_examples(photo(),items(),'batch-incomplete',rights_confirmed=True)
    learning.review_sample(d['example_ids'][0],'approved')
    result=build_export(store/'data.sqlite',store/'output')
    assert result['classification_crops']==1
    assert result['detection_images']==0
    assert result['skipped_incomplete_detection_reviews']==1

def test_mixed_plates_without_boxes_not_single_class_training(store):
    bad=[{**i,'bbox':None} for i in items()]
    d=learning.create_examples(photo(),bad,'batch-mixed-no-boxes',rights_confirmed=True)
    for sid in d['example_ids']:learning.review_sample(sid,'approved')
    result=build_export(store/'data.sqlite',store/'output')
    assert result['classification_crops']==0
    assert result['detection_images']==0
    assert result['skipped_mixed_without_boxes']==2

def test_empty_database_does_not_claim_model_accuracy(store):
    status=evaluate(store/'data.sqlite')
    assert status['status']=='insufficient_data'
    assert status['accuracy'] is None
