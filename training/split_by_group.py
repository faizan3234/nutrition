"""Leakage-resistant train/val/test split by meal or source-photo group.

Input CSV: image_path,label,group_id[,source,license]
Every group_id (one physical meal / duplicate near-identical source) is assigned
as a whole. Output is manifest CSVs, without copying image copyrights.

python -m training.split_by_group images.csv --out dataset/split_manifests
"""
import argparse
from collections import defaultdict
import csv
import hashlib
from pathlib import Path


def split_rows(rows):
    if not rows:raise ValueError('No rows')
    grouped=defaultdict(list)
    for row in rows:
        for key in ('image_path','label','group_id'):
            if not row.get(key):raise ValueError('Missing '+key)
        grouped[row['group_id']].append(row)
    groups=sorted(grouped,key=lambda s:hashlib.sha256(('reliv:2026:'+s).encode()).hexdigest())
    n=len(groups)
    if n<10:raise ValueError('At least ten independent meal groups required')
    train_n=round(n*0.7);val_n=round(n*0.15)
    selected={'train':groups[:train_n],'val':groups[train_n:train_n+val_n],
              'test':groups[train_n+val_n:]}
    if any(not v for v in selected.values()):raise ValueError('Insufficient groups')
    return {key:[row for g in groups_ for row in grouped[g]] for key,groups_ in selected.items()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv');p.add_argument('--out',required=True)
    a=p.parse_args();source=Path(a.csv)
    with source.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        rows=list(reader)
    if not fields:raise ValueError('Empty CSV')
    result=split_rows(rows)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    for key,data in result.items():
        with (out/f'{key}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(data)
        print(key,len(data),'images',len({v['group_id'] for v in data}),'independent groups')

if __name__=='__main__':main()
