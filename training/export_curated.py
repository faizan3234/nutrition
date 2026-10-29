"""Export admin-approved examples into isolated classification and YOLO datasets.

Requires real admin-labeled photographs with permission to train. Never mixes
photos from the same human-defined collection session across train/val/test.
NO trained model/accuracy is produced by this export.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import shutil
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image

VALID_SPLITS = ('train','validation','test')

def slug(label: str) -> str:
    import re
    result=re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-')
    if not result:raise ValueError('Empty food label')
    return result


def build_export(db_path: Path, output: Path) -> dict:
    if not db_path.is_file():raise FileNotFoundError(db_path)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be empty to avoid mixing datasets')
    conn=sqlite3.connect(str(db_path));conn.row_factory=sqlite3.Row
    try:
        rows=[dict(r) for r in conn.execute('''SELECT p.id photo_id,p.image_path,p.image_sha,p.photo_group,p.dataset_split,p.plate_diameter_cm,p.rights_attested,
            e.id,e.name,e.recipe_variant,e.grams,e.kcal,e.protein,e.carbs,e.fat,e.bbox_json,
            e.source_kind,e.evidence_url,e.weight_basis,e.status
            FROM learning_photos p JOIN learning_examples e ON e.photo_id=p.id ORDER BY p.id,e.id''')]
    finally:conn.close()
    by_photo=defaultdict(list)
    for r in rows:by_photo[r['photo_id']].append(r)
    # Fail closed on duplicate images placed across split boundaries.
    sha_split={}
    for batch in by_photo.values():
        sample=batch[0]; key=sample['image_sha']; split=sample['dataset_split']
        if split not in VALID_SPLITS:raise ValueError('Invalid dataset split')
        if key in sha_split and sha_split[key]!=split:
            raise ValueError('Exact photo appears in different training and evaluation splits')
        sha_split[key]=split
    all_approved=[r for r in rows if r['status']=='approved' and r['rights_attested']==1]
    # Labels are stable for a single export and are recorded in label mapping.
    labels=sorted({slug(r['name']) for r in all_approved})
    label_to_idx={label:i for i,label in enumerate(labels)}
    report={'approved_examples':len(all_approved),'photos':len(by_photo), 'classification_crops':0,
            'detection_images':0,'detection_boxes':0,'skipped_mixed_without_boxes':0,
            'skipped_incomplete_detection_reviews':0,'split_classification':{},
            'split_detection':{},'labels':labels,
            'note':'Curated training dataset only. Accuracy, mAP, and weighing MAE still require independent evaluation.'}
    output.mkdir(parents=True,exist_ok=True)
    meta=[]
    for batch in by_photo.values():
        p=batch[0];split=p['dataset_split'];approved=[r for r in batch if r['status']=='approved' and r['rights_attested']==1]
        if not approved:continue
        src=Path(p['image_path'])
        if not src.is_file():raise FileNotFoundError('Approved photo missing: '+str(src))
        with Image.open(src) as img:img=img.convert('RGB')
        for r in approved:
            bbox=json.loads(r['bbox_json']) if r['bbox_json'] else None
            # A whole mixed plate may not safely be labeled as a single food.
            if not bbox and len(batch)>1:
                report['skipped_mixed_without_boxes']+=1;continue
            crop=img
            if bbox:
                w,h=img.size
                region=(round(bbox[0]*w),round(bbox[1]*h),round(bbox[2]*w),round(bbox[3]*h))
                crop=img.crop(region)
            label=slug(r['name'])
            out=output/'classification'/split/label/(r['id']+'.jpg')
            out.parent.mkdir(parents=True,exist_ok=True);crop.save(out,quality=88)
            report['classification_crops']+=1
            report['split_classification'][split]=report['split_classification'].get(split,0)+1
            meta.append({'example_id':r['id'],'photo_group':r['photo_group'],'split':split,
                         'label':label,'image_path':str(out.relative_to(output)), 'recorded_grams':r['grams'],
                         'kcal_per_100g':r['kcal'],'protein_per_100g':r['protein'],
                         'source_kind':r['source_kind'],'weight_basis':r['weight_basis'],
                         'plate_diameter_cm':r['plate_diameter_cm'],'rights_attested':r['rights_attested'],'evidence_url':r['evidence_url']})
        if len(approved)!=len(batch):
            report['skipped_incomplete_detection_reviews']+=1;continue
        if not all(r['bbox_json'] for r in batch):continue
        im_path=output/'detector'/'images'/split/(p['photo_id']+'.jpg')
        im_path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,im_path)
        label_path=output/'detector'/'labels'/split/(p['photo_id']+'.txt')
        label_path.parent.mkdir(parents=True,exist_ok=True)
        lines=[]
        for r in approved:
            x1,y1,x2,y2=json.loads(r['bbox_json'])
            lines.append(f"{label_to_idx[slug(r['name'])]} {(x1+x2)/2:.6f} {(y1+y2)/2:.6f} {x2-x1:.6f} {y2-y1:.6f}")
        label_path.write_text('\n'.join(lines)+'\n')
        report['detection_images']+=1
        report['detection_boxes']+=len(lines)
        report['split_detection'][split]=report['split_detection'].get(split,0)+1
    (output/'labels.json').write_text(json.dumps(label_to_idx,indent=2)+'\n')
    (output/'export_report.json').write_text(json.dumps(report,indent=2)+'\n')
    with (output/'source_manifest.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['example_id','photo_group','split','label','image_path','recorded_grams','kcal_per_100g','protein_per_100g','source_kind','weight_basis','plate_diameter_cm','rights_attested','evidence_url'])
        writer.writeheader();writer.writerows(meta)
    data_yaml="path: " + str((output/'detector').resolve()) + "\ntrain: images/train\nval: images/validation\ntest: images/test\nnames:\n" + ''.join(f"  {i}: '{label}'\n" for i,label in enumerate(labels))
    (output/'detector'/'data.yaml').parent.mkdir(parents=True,exist_ok=True)
    (output/'detector'/'data.yaml').write_text(data_yaml)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Export curated admin learning data (not trained model)')
    parser.add_argument('--db',default='nutrition.sqlite3')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(build_export(Path(args.db),Path(args.output)),indent=2))
