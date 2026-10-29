"""Create measured 100g-vs-300g training/evaluation pairs from approved photos.

Only *scale*-weighed amounts count as mass ground truth. Similar photos by
visual appearance with unweighed serving sizes are not usable for weight MAE.
The script prepares labeled pairs; it does NOT train a mass estimator.
"""
from __future__ import annotations
import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from itertools import combinations
from pathlib import Path

def generate(db:Path,out:Path,ratio:float=2.2):
    if ratio <= 1:raise ValueError('Ratio threshold must exceed 1')
    with sqlite3.connect(str(db)) as conn:
        conn.row_factory=sqlite3.Row
        rows=[dict(x) for x in conn.execute('''SELECT e.id, e.name,e.recipe_variant,e.grams,e.weight_basis,
           p.id photo_id,p.image_path,p.photo_group,p.dataset_split,p.plate_diameter_cm
           FROM learning_examples e JOIN learning_photos p ON p.id=e.photo_id
           WHERE e.status='approved' AND e.weight_basis='scale' AND p.rights_attested=1 ORDER BY p.photo_group''')]
    groups=defaultdict(list)
    for r in rows:groups[(r['photo_group'],r['name'].casefold(),r['recipe_variant'].casefold())].append(r)
    pairs=[]
    for (group,name,variant),examples in groups.items():
        for a,b in combinations(examples,2):
            if a['photo_id']==b['photo_id']:continue
            small,large=sorted((a,b),key=lambda x:x['grams'])
            if large['grams']/small['grams']<ratio:continue
            pairs.append({'label':name,'recipe_variant':variant,'group':group,'split':a['dataset_split'],
                          'small_image':small['image_path'],'large_image':large['image_path'],
                          'small_grams':small['grams'],'large_grams':large['grams'],
                          'small_plate_cm':small['plate_diameter_cm'],'large_plate_cm':large['plate_diameter_cm'],
                          'ratio':round(large['grams']/small['grams'],3)})
    if out.exists():raise ValueError('Refusing to overwrite existing pair dataset')
    out.parent.mkdir(parents=True,exist_ok=True)
    columns=['label','recipe_variant','group','split','small_image','large_image','small_grams','large_grams','small_plate_cm','large_plate_cm','ratio']
    with out.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader();writer.writerows(pairs)
    return {'scale_weighed_examples':len(rows),'mass_ratio_pairs':len(pairs),
            'pair_file':str(out),'status':'prepared_no_model_trained',
            'note':'For model training & independent portion testing; not evidence of accuracy.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',default='nutrition.sqlite3');p.add_argument('--out',required=True);a=p.parse_args()
    print(json.dumps(generate(Path(a.db),Path(a.out)),indent=2))
