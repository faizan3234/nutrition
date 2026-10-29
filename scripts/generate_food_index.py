"""Rebuild the official list of *searchable foods*, not camera-recognized labels."""
from collections import defaultdict
from datetime import date
import csv
from pathlib import Path
from app.catalog import FOODS

OUT=Path(__file__).resolve().parent.parent/'docs'

def write():
    OUT.mkdir(exist_ok=True)
    keys=['name','category','aliases','default_grams','kcal','protein','carbs','fat','source']
    with (OUT/'SUPPORTED_FOODS.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys,lineterminator="\n");writer.writeheader()
        for food in sorted(FOODS,key=lambda x:(x['category'],x['name'])):
            writer.writerow({**{k:food[k] for k in keys if k!='aliases'},'aliases':', '.join(food['aliases'])})
    categories=defaultdict(list)
    for f in FOODS: categories[f['category']].append(f['name'])
    contents=['# Reliv Nutrition AI — searchable food catalogue',
        '',f'**{len(FOODS)} searchable and loggable example foods · generated {date.today().isoformat()}**',
        '', '**This is NOT a list of camera-recognized categories.** The per-100g starter',
        'nutrition values are illustrative and do not constitute food-laboratory validation.',
        '', 'Branded drinks, shakes and packaged foods are looked up by exact brand/variant/barcode',
        'from Open Food Facts when an Internet connection is available. This is an open-ended',
        'product lookup, not a pre-validated fixed list of products.', '',
        '| Category | Count | Food names |','|---|---:|---|']
    for category,names in sorted(categories.items()):
        contents.append(f'| {category} | {len(names)} | {", ".join(sorted(names))} |')
    (OUT/'SUPPORTED_FOODS.md').write_text('\n'.join(contents)+'\n',encoding='utf-8')
    return len(FOODS)

if __name__=='__main__':print(write())
