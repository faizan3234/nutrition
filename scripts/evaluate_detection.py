"""Class-aware object-detection benchmark for held-out multi-food plates.

Usage:
  python -m scripts.evaluate_detection --ground-truth heldout_gt.json \
      --predictions heldout_predictions.json --out detection_metrics.json

Inputs are JSON lists with image_id, label, bbox=[x1,y1,x2,y2]; predictions
also need score in [0,1]. Coordinates must share the same reference image.
Model predictions MUST be generated on a held-out dataset. Sample test data
in tests/ are mathematical fixtures, not food-recognition evaluation.
"""
import argparse
from collections import defaultdict
import json
import math
from statistics import mean

IOU_THRESHOLDS = [0.50+i*0.05 for i in range(10)]


def iou(a,b):
    x1=max(a[0],b[0]);y1=max(a[1],b[1]);x2=min(a[2],b[2]);y2=min(a[3],b[3])
    overlap=max(0,x2-x1)*max(0,y2-y1)
    area=lambda q:max(0,q[2]-q[0])*max(0,q[3]-q[1])
    union=area(a)+area(b)-overlap
    return overlap/union if union>0 else 0.0


def validate(rows,prediction=False):
    for row in rows:
        if not all(k in row for k in ('image_id','label','bbox')) or not isinstance(row['bbox'],list) or len(row['bbox'])!=4:
            raise ValueError('Each item needs image_id, label and bbox [x1,y1,x2,y2]')
        try: box=[float(v) for v in row['bbox']]
        except (TypeError,ValueError):raise ValueError('Non-numeric bounding box')
        if not all(math.isfinite(v) for v in box) or box[2]<=box[0] or box[3]<=box[1]:
            raise ValueError('Invalid bounding box')
        if prediction and (not isinstance(row.get('score'),(float,int)) or not 0<=row['score']<=1):
            raise ValueError('Prediction requires score between 0 and 1')


def class_ap(gt,pred,threshold):
    if not gt:return None
    gt_by_image=defaultdict(list)
    for g in gt: gt_by_image[str(g['image_id'])].append(g['bbox'])
    matched=defaultdict(set)
    pred=sorted(pred,key=lambda r:r['score'],reverse=True)
    tps=[];fps=[]
    for p in pred:
        candidates=gt_by_image.get(str(p['image_id']),[])
        best=-1;best_iou=-1
        for idx,b in enumerate(candidates):
            if idx in matched[str(p['image_id'])]:continue
            value=iou(b,p['bbox'])
            if value>best_iou:best=idx;best_iou=value
        if best>=0 and best_iou>=threshold-1e-9:
            matched[str(p['image_id'])].add(best);tps.append(1);fps.append(0)
        else:tps.append(0);fps.append(1)
    if not pred:return 0.0
    recalls=[];precisions=[];tp=0;fp=0
    for t,f in zip(tps,fps):
        tp+=t;fp+=f
        recalls.append(tp/len(gt));precisions.append(tp/(tp+fp))
    # COCO-style 101 point interpolated average precision.
    return sum(max((p for p,r in zip(precisions,recalls) if r>=level-1e-10),default=0) for level in (i/100 for i in range(101)))/101


def evaluate_detection(ground_truth,predictions):
    validate(ground_truth);validate(predictions,True)
    if not ground_truth:raise ValueError('No ground truth boxes')
    classes=sorted({x['label'] for x in ground_truth})
    category={}
    for label in classes:
        g=[x for x in ground_truth if x['label']==label]
        p=[x for x in predictions if x['label']==label]
        vals=[class_ap(g,p,t) for t in IOU_THRESHOLDS]
        category[label]={'ground_truth_instances':len(g),'predicted_boxes':len(p),
                         'AP50':round(vals[0],4),'AP50_95':round(mean(vals),4)}
    return {'ground_truth_instances':len(ground_truth),'prediction_boxes':len(predictions),
            'distinct_images':len({x['image_id'] for x in ground_truth}),
            'categories_with_ground_truth':len(classes),
            'mAP50':round(mean(c['AP50'] for c in category.values()),4),
            'mAP50_95':round(mean(c['AP50_95'] for c in category.values()),4),
            'unknown_class_predictions':sum(x['label'] not in classes for x in predictions),
            'per_class':category,
            'caution':'Metrics measure only these supplied images and prediction boxes. They do not measure portion mass or nutrient accuracy.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ground-truth',required=True);p.add_argument('--predictions',required=True);p.add_argument('--out')
    args=p.parse_args()
    with open(args.ground_truth) as f:gt=json.load(f)
    with open(args.predictions) as f:pred=json.load(f)
    result=evaluate_detection(gt,pred)
    payload=json.dumps(result,indent=2)
    if args.out:
        with open(args.out,'w') as f:f.write(payload)
    print(payload)

if __name__=='__main__':main()
