"""Evaluate crude near-duplicate reference retrieval on real held-out photo groups.

This is NOT a trained food detector and cannot report object-detection mAP.
Restricts reference index to TRAIN only and evaluates on TEST or VALIDATION.
No benchmarks are claimed if no held-out samples exist.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path
from PIL import Image
from app.learning import dhash

def evaluate(db_path: Path, test_split='test', max_distance=5):
    if test_split not in ('test','validation'):
        raise ValueError('Heldout split must be test or validation')
    with sqlite3.connect(str(db_path)) as con:
        con.row_factory=sqlite3.Row
        rows=[dict(row) for row in con.execute('''SELECT p.image_sha,p.dhash,p.image_path,p.dataset_split,p.photo_group,p.rights_attested,
               e.name,e.status FROM learning_photos p JOIN learning_examples e ON e.photo_id=p.id''')]
    train=[r for r in rows if r['status']=='approved' and r['rights_attested']==1 and r['dataset_split']=='train']
    held=[r for r in rows if r['status']=='approved' and r['rights_attested']==1 and r['dataset_split']==test_split]
    if not train or not held:return {'status':'insufficient_data','train_examples':len(train),
                                     'heldout_examples':len(held),'accuracy':None,'abstentions':None}
    if set(r['photo_group'] for r in held) & set(r['photo_group'] for r in train):
        raise ValueError('Group leakage detected')
    if set(r['image_sha'] for r in held) & set(r['image_sha'] for r in train):
        raise ValueError('Duplicate photo leaked into heldout evaluation')
    top1=0;answered=0
    for row in held:
        candidates=sorted((((int(row['dhash'],16)^int(r['dhash'],16)).bit_count(),r) for r in train), key=lambda pair:pair[0])
        if candidates and candidates[0][0] <= max_distance:
            answered+=1
            top1+=int(candidates[0][1]['name'].casefold()==row['name'].casefold())
    return {'status':'measured_near_duplicate_retrieval_only','train_examples':len(train),
        'heldout_examples':len(held),'answered':answered,'correct_of_answered':top1,
        'top1_precision_when_answering':round(top1/answered,4) if answered else None,
        'coverage':round(answered/len(held),4),
        'top1_accuracy_all_heldout':round(top1/len(held),4),
        'food_detector_map':None,'portion_weight_mae':None,'calorie_mae':None,
        'warning':'This measures near-image retrieval only, NOT food detector accuracy or gram estimation.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--db',default='nutrition.sqlite3');parser.add_argument('--split',choices=['test','validation'],default='test');parser.add_argument('--out')
    a=parser.parse_args();r=evaluate(Path(a.db),a.split);result=json.dumps(r,indent=2)
    if a.out:Path(a.out).write_text(result+'\n')
    print(result)
