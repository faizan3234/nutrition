"""USDA FoodData Central search, keeping only per-100g laboratory/reference records.

Requires operator FDC_API_KEY. USDA FDC data are CC0/public domain.
Source: https://fdc.nal.usda.gov/api-guide/
"""
from __future__ import annotations
import json
import os
import urllib.request
from urllib.parse import urlencode

ENDPOINT='https://api.nal.usda.gov/fdc/v1/foods/search'
# FoodData Central nutrient IDs; these nutrients are grams, energy kcal.
IDS={'kcal':(1008,2047,2048),'protein':(1003,),'fat':(1004,),'carbs':(1005,)}

def normalize_fdc(entry):
    if entry.get('dataType') not in ('Foundation','SR Legacy','Survey (FNDDS)'):
        return None
    per={}
    for val in entry.get('foodNutrients',[]):
        id=val.get('nutrientId') or (val.get('nutrient') or {}).get('id')
        amount=val.get('value',val.get('amount'))
        try:amount=float(amount)
        except (TypeError,ValueError):continue
        if amount<0 or amount>1000:continue
        for key,ids in IDS.items():
            if id in ids and key not in per:per[key]=amount
    if not all(x in per for x in IDS):return None
    desc=str(entry.get('description') or '')[:200]
    if not desc:return None
    return {'fdc_id':entry['fdcId'],'name':desc,'category':entry['dataType'],
            'unit':'g','per_100g':{key:round(per[key],2) for key in IDS},
            'source':'USDA FoodData Central ('+entry['dataType']+')',
            'source_url':'https://fdc.nal.usda.gov/food-details/'+str(entry['fdcId'])+'/nutrients',
            'nutrition_verified_for_listing':True,
            'warning':'Values match the specified USDA preparation (raw/cooked/etc). Not automatically valid for Indian restaurant recipes.'}

def search_usda(query,limit=10):
    key=os.getenv('FDC_API_KEY','').strip()
    if not key:raise RuntimeError('USDA API key not configured')
    if not 2<=len(query.strip())<=100:raise ValueError('Query must be 2–100 characters')
    params=urlencode({'api_key':key,'query':query.strip(),'pageSize':min(limit*3,30),
                        'dataType':['Foundation','SR Legacy','Survey (FNDDS)']},doseq=True)
    req=urllib.request.Request(ENDPOINT+'?'+params,headers={'User-Agent':'RelivNutritionAI/0.5 (relivkiosk.vercel.app)'})
    try:
        with urllib.request.urlopen(req,timeout=12) as resp:body=json.load(resp)
    except (OSError,ValueError) as e:raise RuntimeError('USDA nutrition database currently unavailable') from e
    ans=[]
    for food in body.get('foods',[]):
        normalized=normalize_fdc(food)
        if normalized:ans.append(normalized)
        if len(ans)>=limit:break
    return ans

def lookup_usda(fdc_id:int):
    if not 1<=fdc_id<=1_000_000_000:raise ValueError('Invalid USDA food ID')
    key=os.getenv('FDC_API_KEY','').strip()
    if not key:raise RuntimeError('USDA API key not configured')
    url='https://api.nal.usda.gov/fdc/v1/food/'+str(fdc_id)+'?'+urlencode({'api_key':key})
    request=urllib.request.Request(url,headers={'User-Agent':'RelivNutritionAI/0.5 (relivkiosk.vercel.app)'})
    try:
        with urllib.request.urlopen(request,timeout=12) as r:body=json.load(r)
    except (OSError,ValueError) as e:raise RuntimeError('USDA food detail temporarily unavailable') from e
    result=normalize_fdc(body)
    if result is None:raise LookupError('Complete source-backed per-100g nutrition unavailable for this record')
    return result
