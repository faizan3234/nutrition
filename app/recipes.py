"""Weighed ingredient/recipe builder with provenance-preserving numeric estimates."""
from decimal import Decimal, ROUND_HALF_UP
from .catalog import LOOKUP

NUTRIENTS=('kcal','protein','carbs','fat')
def calculate_recipe(ingredients:list[dict],cooked_yield_g:float|None):
    if not 1<=len(ingredients)<=50:raise ValueError('Provide 1–50 ingredients')
    totals={n:Decimal(0) for n in NUTRIENTS};sources=[]
    safety_warnings=[]
    seen=set()
    prepared_bases=[]
    extras=[]
    for i,entry in enumerate(ingredients):
        g=entry.get('grams')
        if isinstance(g,bool) or not isinstance(g,(int,float)) or not 0<g<=15000:raise ValueError(f'Invalid ingredient grams at #{i+1}')
        f=LOOKUP.get(entry.get('food_id',''))
        if f:
            per100={n:f[n] for n in NUTRIENTS}
            source='illustrative_generic_food'
        else:
            per100=entry.get('per100')
            if not isinstance(per100,dict) or not entry.get('source_note'):
                raise ValueError(f'Ingredient #{i+1} needs known food ID or explicit nutrition label with source')
            if any(n not in per100 or isinstance(per100[n],bool) or not isinstance(per100[n],(int,float)) or not 0<=per100[n]<=950 for n in NUTRIENTS):
                raise ValueError(f'Invalid nutrition label for ingredient #{i+1}')
            source='user_label_unverified'
        key=(entry.get('food_id') or entry.get('name') or '').casefold().strip()
        if key and key in seen:
            safety_warnings.append(f'Duplicate ingredient {key}: confirm it was deliberately added twice')
        seen.add(key)
        role=entry.get('role','ingredient')
        if role not in ('ingredient','prepared_base','added_fat','topping'):
            raise ValueError('Invalid ingredient role')
        preparation=entry.get('preparation','as_served')
        if preparation not in ('raw','cooked','as_served'):
            raise ValueError('Specify raw, cooked or as_served')
        if role=='prepared_base':prepared_bases.append(key)
        if role in ('added_fat','topping'):extras.append(key)
        for n in NUTRIENTS:totals[n]+=Decimal(str(per100[n]))*Decimal(str(g))/100
        sources.append({'ingredient':entry.get('food_id') or entry.get('name') or str(i+1),'grams':g,'source':source,'role':role,'preparation':preparation})
    if prepared_bases and extras:safety_warnings.append('Prepared dish may already contain oil, cheese or sauce: check toppings are not double-counted')
    if any(x['preparation']=='raw' for x in sources) and any(x['preparation']=='cooked' for x in sources) and cooked_yield_g is None:
        safety_warnings.append('Raw/cooked weights are mixed; enter final cooked yield before interpreting per-100g cooked nutrients')
    if cooked_yield_g is not None and not 0<cooked_yield_g<=100000:raise ValueError('Invalid cooked yield')
    def rnd(x):return float(x.quantize(Decimal('.1'), rounding=ROUND_HALF_UP))
    result={'total':{n:rnd(totals[n]) for n in NUTRIENTS},'ingredients':sources,
            'cooked_yield_g':cooked_yield_g,'nutrition_verified':False,'safety_warnings':safety_warnings,
            'warning':'Nutrition is based on ingredient input, not lab analysis. Include oils, sauces and cooking losses.'}
    if cooked_yield_g:
        result['per_100g_cooked']={n:rnd(totals[n]*100/Decimal(str(cooked_yield_g))) for n in NUTRIENTS}
    return result
