import pytest
from scripts.evaluate_detection import iou, class_ap, evaluate_detection

G=[{'image_id':'img1','label':'dosa','bbox':[0,0,100,100]},
   {'image_id':'img2','label':'rice','bbox':[25,25,85,85]}]

def test_iou_correct():
    assert iou([0,0,10,10],[0,0,10,10])==1
    assert iou([0,0,10,10],[20,20,30,30])==0
    assert abs(iou([0,0,10,10],[5,5,15,15])-25/175)<1e-9

def test_map_perfect_predictions():
    result=evaluate_detection(G,[{**g,'score':0.9} for g in G])
    assert result['mAP50']==result['mAP50_95']==1
    assert result['distinct_images']==2

def test_map_empty_predictions():
    result=evaluate_detection(G,[])
    assert result['mAP50']==0
    assert result['mAP50_95']==0

def test_map_wrong_class_does_not_match():
    p=[{'image_id':'img1','label':'rice','bbox':[0,0,100,100],'score':0.99}]
    result=evaluate_detection(G,p)
    assert result['mAP50']==0

def test_duplicate_penalizes_precision_if_highest_scored_wrong():
    gt=[G[0]]
    preds=[{'image_id':'img1','label':'dosa','bbox':[0,0,10,10],'score':0.99},
           {'image_id':'img1','label':'dosa','bbox':[0,0,100,100],'score':0.6}]
    assert 0<class_ap(gt,preds,0.5)<1

def test_incomplete_nonfinite_annotations_rejected():
    with pytest.raises(ValueError):evaluate_detection(G,[{'image_id':'img1','label':'dosa','bbox':[0,0,0,10],'score':0.8}])
    with pytest.raises(ValueError):evaluate_detection(G,[{'image_id':'img1','label':'dosa','bbox':[0,0,100,100],'score':float('nan')}])
