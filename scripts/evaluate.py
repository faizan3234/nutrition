"""Evaluate predicted food mass and nutrients against independently weighed ground truth.

CSV columns: meal_id,true_grams,predicted_grams,true_kcal,predicted_kcal,
             true_protein,predicted_protein

This script evaluates only rows with real predictions. It does not imply that
Reliv generates image-derived weights without a configured model.
"""
from __future__ import annotations
import argparse
import csv
import json
from statistics import mean,median

METRICS = ('grams', 'kcal', 'protein')
FIELDS = ['meal_id']+[f'{kind}_{unit}' for unit in METRICS for kind in ('true','predicted')]


def evaluate(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError('Evaluation requires at least one matched predicted component.')
    results = {'components':len(rows), 'distinct_meals':len({r['meal_id'] for r in rows}), 'metrics':{}}
    for unit in METRICS:
        actual = [float(r[f'true_{unit}']) for r in rows]
        predicted = [float(r[f'predicted_{unit}']) for r in rows]
        if any(v < 0 for v in actual+predicted):
            raise ValueError(f'Negative {unit} measurement in benchmark.')
        absolute_errors=[abs(a-p) for a,p in zip(actual,predicted)]
        pct_errors=[abs(a-p)/a*100 for a,p in zip(actual,predicted) if a>0]
        results['metrics'][unit]={
            'mean_absolute_error':round(mean(absolute_errors),4),
            'median_absolute_error':round(median(absolute_errors),4),
            'mean_absolute_percentage_error_nonzero_truth':round(mean(pct_errors),4) if pct_errors else None,
            'nonzero_reference_count':len(pct_errors),
        }
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv',help='Independent validation CSV')
    parser.add_argument('--json',action='store_true',help='Print machine-readable JSON')
    args=parser.parse_args()
    with open(args.csv,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        missing=[field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:parser.error('Missing columns: '+', '.join(missing))
        rows=list(reader)
    try:result=evaluate(rows)
    except ValueError as e:parser.error(str(e))
    print(json.dumps(result,indent=2) if args.json else _format(result))


def _format(r):
    lines=[f"Matched components: {r['components']}; meals: {r['distinct_meals']}"]
    for unit,v in r['metrics'].items():
        lines.append(f"{unit}: MAE {v['mean_absolute_error']:.2f}, MedianAE {v['median_absolute_error']:.2f}, "
                     f"MAPE {v['mean_absolute_percentage_error_nonzero_truth']}% (nonzero truth)")
    return '\n'.join(lines)

if __name__=='__main__':main()
