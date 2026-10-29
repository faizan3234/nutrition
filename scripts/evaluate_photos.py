"""Run a configured vision model on labeled, rights-cleared single-food images.

CSV: image_path,true_food_name[,true_grams,true_kcal,true_protein]
No model weights, photos, or predictions are silently synthesized.

Example:
  VISION_PROVIDER=nutrilens NUTRILENS_WEIGHTS=... NUTRILENS_LABELS=... \
    python -m scripts.evaluate_photos /data/test_images.csv --out /tmp/results.json

For mixed dishes use separate multi-item detection evaluation with box/instance labels.
"""
from __future__ import annotations
import argparse
import base64
import csv
import json
import os
from pathlib import Path
from statistics import mean
from app.catalog import find_food
from app.vision import analyze


def benchmark(rows, base:Path, fn=analyze):
    if os.getenv('VISION_PROVIDER','none').lower()=='none' and fn==analyze:
        raise RuntimeError('No vision model configured: set VISION_PROVIDER and model weights/credentials first.')
    output=[]
    for row in rows:
        image=base/row['image_path']
        if not image.is_file():raise FileNotFoundError(image)
        truth=find_food(row['true_food_name'])
        if truth is None:raise ValueError('No catalogue mapping for true food: '+row['true_food_name'])
        response=fn(base64.b64encode(image.read_bytes()).decode())
        guesses=response.get('items') or []
        top=guesses[0] if guesses else {}
        label=(top.get('food') or {}).get('id')
        pred_weight=top.get('grams') if top.get('portion_method')=='uncalibrated_photo_estimate' else None
        pred_weight=float(pred_weight) if pred_weight is not None else None
        actual_weight=float(row['true_grams']) if row.get('true_grams') else None
        # Calorie and protein errors require true outcomes and a valid estimate;
        # photos scored with default grams are not credited as weight inference.
        record={'image_path':row['image_path'],'true_food':truth['id'],'predicted_food':label,
                'recognized':label==truth['id'],'true_grams':actual_weight,
                'predicted_grams':pred_weight,'weight_error_grams':abs(pred_weight-actual_weight)
                 if pred_weight is not None and actual_weight is not None else None}
        for field,key in [('kcal','kcal'),('protein','protein')]:
            reference=float(row['true_'+field]) if row.get('true_'+field) else None
            if reference is not None and pred_weight is not None and top.get('food'):
                from app.catalog import nutrients
                guess=nutrients(top['food'],pred_weight)[key]
                record['error_'+field]=abs(guess-reference)
            else:record['error_'+field]=None
        output.append(record)
    counted=len(output)
    weight_errors=[r['weight_error_grams'] for r in output if r['weight_error_grams'] is not None]
    calorie_errors=[r['error_kcal'] for r in output if r['error_kcal'] is not None]
    protein_errors=[r['error_protein'] for r in output if r['error_protein'] is not None]
    return {'evaluated_images':counted,'top1_recognition_accuracy_percent':round(100*sum(r['recognized'] for r in output)/counted,2) if counted else None,
            'weight_estimates_evaluated':len(weight_errors),'weight_mae_grams':round(mean(weight_errors),2) if weight_errors else None,
            'calorie_estimates_evaluated':len(calorie_errors),'calorie_mae_kcal':round(mean(calorie_errors),2) if calorie_errors else None,
            'protein_estimates_evaluated':len(protein_errors),'protein_mae_grams':round(mean(protein_errors),2) if protein_errors else None,
            'per_image':output}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',help='CSV of image_path,true_food_name[,true_grams,true_kcal,true_protein]')
    parser.add_argument('--out',default=None,help='Save JSON report file')
    args=parser.parse_args();path=Path(args.csv).resolve()
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        for key in ('image_path','true_food_name'):
            if key not in (reader.fieldnames or []):parser.error('Missing column '+key)
        data=list(reader)
    if not data:parser.error('No samples in benchmark CSV')
    try:r=benchmark(data,path.parent)
    except (ValueError,RuntimeError,FileNotFoundError) as e:parser.error(str(e))
    payload=json.dumps(r,indent=2)
    if args.out:Path(args.out).write_text(payload,encoding='utf-8')
    print(payload)

if __name__=='__main__':main()
