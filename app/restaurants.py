"""Restaurant name matching with source attribution, NEVER invented restaurant macros.

Official menu pages establish that a dish is sold, not its nutrition.
Operators can supply their own audited, evidence-backed CSV later.
"""
from __future__ import annotations
import csv
import os
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from .catalog import LOOKUP

MENU = [
 ('Arsalan','Chicken Biryani','biryani-chicken','https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Mutton Biryani','biryani-mutton','https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Egg Biryani',None,'https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Veg Biryani','biryani-veg','https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Biryani Rice',None,'https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Chicken Qorma','chicken-curry','https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Mutton Qorma','mutton-curry','https://arsalanrestaurants.com/menu/',None),
 ('Arsalan','Paneer Tikka Kebab','paneer-tikka','https://arsalanrestaurants.com/menu/',None),
 ('Biryani By Kilo','Chicken Hyderabadi Dum Biryani [1/2 kg]','hyderabadi-biryani','https://biryanibykilo.com/item-1590/22-chicken-hyderabadi-dum-biryani',500),
 ('Biryani By Kilo','Chicken Hyderabadi Dum Biryani [1 kg]','hyderabadi-biryani','https://biryanibykilo.com/item-1590/22-chicken-hyderabadi-dum-biryani',1000),
 ('Biryani By Kilo','Veg Hyderabadi Biryani [1/2 kg]','biryani-veg','https://biryanibykilo.com/item-1590/22-chicken-hyderabadi-dum-biryani',500),
]

def _q(x): return float(Decimal(str(x)).quantize(Decimal('.1'), rounding=ROUND_HALF_UP))

def official_nutrition():
    """Only accept explicit audited rows, not machine-found menu numbers.
    CSV headers: brand,dish,kcal_100g,protein_100g,carbs_100g,fat_100g,
    evidence_url,verified_on,reviewer. Operators validate authenticity separately.
    """
    path=os.getenv('RELIV_RESTAURANT_NUTRITION_CSV','').strip()
    if not path or not Path(path).is_file(): return {}
    out={}
    with open(path,newline='',encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                key=(row['brand'].strip().casefold(),row['dish'].strip().casefold())
                vals={k:float(row[k]) for k in ('kcal_100g','protein_100g','carbs_100g','fat_100g')}
                if any(not 0<=v<=950 for v in vals.values()):continue
                if not (row.get('evidence_url','').startswith('https://') and row.get('reviewer') and row.get('verified_on')):continue
                out[key]={**vals,'evidence_url':row['evidence_url'],'reviewer':row['reviewer'],'verified_on':row['verified_on']}
            except (KeyError,TypeError,ValueError):continue
    return out

def search_restaurants(q):
    query=q.strip().casefold()
    if len(query)<2:return []
    audited=official_nutrition()
    items=[]
    for brand,dish,generic,menu_url,pack_size in MENU:
        if query not in (brand+' '+dish).casefold():continue
        nutrition=audited.get((brand.casefold(),dish.casefold()))
        items.append({'id':brand.lower().replace(' ','-')+':'+dish.lower().replace(' ','-'),
            'brand':brand,'dish':dish,'menu_url':menu_url,'verified_menu_item':True,
            'nutrition':nutrition,'nutrition_verified_for_specific_dish':bool(nutrition),
            'generic_food_id':generic if generic in LOOKUP else None,
            'advertised_pack_weight_g':pack_size,
            'warning':('Nutrition audited against linked evidence' if nutrition else
                       'Official menu identifies the dish, but no restaurant-specific nutrition values were verified. Generic recipe is an ESTIMATE only.')})
    return items[:30]

def estimate_restaurant(brand,dish,grams,use_generic=False):
    if not 0 < grams<=5000:raise ValueError('Invalid serving weight')
    match=next((r for r in search_restaurants(brand) if r['brand'].casefold()==brand.strip().casefold() and r['dish'].casefold()==dish.strip().casefold()),None)
    if not match:raise LookupError('Restaurant dish not in sourced menu catalogue')
    if match['nutrition']:
        n=match['nutrition']; return {'brand':brand,'dish':dish,'grams':grams,'unit':'g',
              'nutrition':{'kcal':_q(n['kcal_100g']*grams/100),'protein':_q(n['protein_100g']*grams/100),'carbs':_q(n['carbs_100g']*grams/100),'fat':_q(n['fat_100g']*grams/100)},
              'source':'audited_restaurant_nutrition','evidence_url':n['evidence_url'], 'is_restaurant_specific':True}
    if not use_generic:
        return {'brand':brand,'dish':dish,'grams':grams,'nutrition':None,'requires_explicit_generic_opt_in':True,
                'warning':'Restaurant-specific calories/protein unavailable. Confirm weight and explicitly opt into a generic estimate.'}
    from .catalog import nutrients
    food=LOOKUP.get(match['generic_food_id'])
    if not food:raise LookupError('No comparable generic dish')
    return {'brand':brand,'dish':dish,'grams':grams,'unit':'g','nutrition':nutrients(food,grams),
            'source':'illustrative_generic_recipe','is_restaurant_specific':False,'evidence_url':match['menu_url'],
            'warning':'NOT Arsalan/BBK measured nutrition: recipe and portion may differ substantially.'}
