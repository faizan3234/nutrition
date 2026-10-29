"""Reproducible arithmetic correctness audit; NOT a computer-vision accuracy test."""
import json
from decimal import Decimal, ROUND_HALF_UP
from app.catalog import FOODS, nutrients


def check():
    grams=(5,25,50,75,100,150,200,300,500,900)
    checks=[]
    failures=[]
    for f in FOODS:
        for weight in grams:
            actual=nutrients(f,weight)
            for metric in ('kcal','protein','carbs','fat'):
                # Python round() is banker's rounding; calculate the same independently
                # using Decimal of the numeric input (not nutrition-table truth).
                raw=Decimal(str(f[metric]))*Decimal(weight)/Decimal('100')
                expectation=float(raw.quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))
                good=actual[metric]==expectation
                checks.append(good)
                if not good:failures.append([f['name'],weight,metric,expectation,actual[metric]])
    return {'status':'pass' if not failures else 'fail',
            'foods':len(FOODS),'weights_g':grams,
            'nutrient_arithmetic_checks':len(checks),
            'passed':sum(checks),'failed':len(failures),
            'failures':failures[:5],
            'interpretation':'Only verifies deterministic per-100g scaling of illustrative table. No photographed meals, weighed portions, independently measured calories or model predictions were used.'}

if __name__=='__main__':print(json.dumps(check(),indent=2))
