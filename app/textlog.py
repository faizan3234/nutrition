"""Rule-based text-to-food parsing that never makes up SKU macros or photo grams."""
from __future__ import annotations
import re
from .catalog import LOOKUP,FOODS,serving_unit

BRANDS=('coca cola','coca-cola','coke','epigamia','pepsi','amul','red bull','biryani by kilo','arsalan','kareems',"kareem's")
STOPWORDS={'i','ate','had','drank','drink','of','some','a','an','the','for','lunch','breakfast','dinner','snack','please','track','log','my','with'}
UNITS={'g':'g','gram':'g','grams':'g','gm':'g','gms':'g','ml':'ml','millilitre':'ml','millilitres':'ml'}

def _amount(text):
    m=re.search(r'(?<!\w)(\d+(?:\.\d+)?)\s*(grams?|gms?|gm|g|millilitres?|millilitres?|ml)\b',text,re.I)
    if m:
        value=float(m.group(1)); return (value,UNITS.get(m.group(2).lower(),'ml' if m.group(2).lower().startswith('milli') else 'g')) if 0<value<=5000 else (None,None)
    return None,None

def parse_entry(text):
    if not isinstance(text,str) or len(text)>250:raise ValueError('Text must have at most 250 characters')
    clean=' '.join(text.lower().strip().split())
    clean=re.sub(r"(?<=\w)['’](?=\w)",'',clean)
    if not clean:raise ValueError('Enter a food or drink')
    amount,unit=_amount(clean)
    # Countable unit: estimated by typical serving only, never claim weighed grams.
    count_match=None
    if amount is None:
        count_match=re.search(r'(?<!\w)([1-9]|1[0-2])\s*(?:pieces?|pcs?|x)?\s+(?=[a-z])',clean)
        if count_match:
            clean=(clean[:count_match.start()]+clean[count_match.end():]).strip()
    clean=re.sub(r'\b\d+(?:\.\d+)?\s*(?:grams?|gms?|gm|g|millilitres?|ml)\b',' ',clean)
    clean=re.sub(r'[^\w\s\-]',' ',clean)
    clean=' '.join(t for t in clean.split() if t not in STOPWORDS)
    brands=sorted((b for b in BRANDS if b.replace('-',' ') in clean.replace('-',' ')),key=len,reverse=True)
    if brands:
        return {'kind':'branded_product_or_restaurant','query':clean,'amount':amount,'unit':unit,
                'brand':brands[0], 'auto_logged':False,
                'message':'Select an exact product barcode/variant or sourced restaurant dish before logging.'}
    # Broad nouns must not silently match an arbitrary variant's short alias.
    if clean in {'pizza','pasta','biryani','burger','dosa','shake','sausage','juice','protein shake',
        'mocktail','mojito','virgin mojito','fried rice','cheesecake','brownie','ice cream','smoothie','milkshake','iced tea','dessert'}:
        candidates=[{'id':f['id'],'name':f['name']} for f in FOODS
                    if clean in (f['name']+' '+' '.join(f['aliases'])).lower()][:20]
        return {'kind':'ambiguous','query':clean,'amount':amount,'unit':unit,
                'candidates':candidates,'auto_logged':False,
                'message':'Select the exact variety before estimating nutrients.'}
    from .vision import match_food_exact
    food=match_food_exact(clean)
    if not food:
        # A partial match can correspond to several recipes (e.g. pizza).
        # Return candidates; DO NOT silently assign the first food's nutrients.
        matches=[]
        for f in FOODS:
            names=[f['name'],*f.get('aliases',[])]
            normalized=[re.sub(r'[^a-z0-9]+',' ',c.casefold()).strip() for c in names]
            if any(v and re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',clean) for v in normalized):
                matches.append(f)
        # Exact normalized matches are already covered above.
        if matches:
            if len(matches)==1:
                food=matches[0]
            else:
                return {'kind':'ambiguous','query':clean,'amount':amount,'unit':unit,
                    'candidates':[{'id':f['id'],'name':f['name']} for f in matches[:15]],
                    'auto_logged':False,'message':'Several food varieties match; select the correct dish first.'}
    if not food:
        return {'kind':'unrecognized','query':clean,'amount':amount,'unit':unit,'auto_logged':False,
                'message':'Choose or add a verified food record; no nutritional guess was generated.'}
    correct_unit=serving_unit(food)
    if unit and unit!=correct_unit:
        return {'kind':'unit_mismatch','food':food,'amount':amount,'unit':unit,'auto_logged':False,
                'message':f'Use {correct_unit} for this entry or a known density to convert.'}
    from .catalog import nutrients
    typical_estimate=food['default_grams']*int(count_match.group(1)) if count_match else None
    chosen=amount if amount is not None else typical_estimate
    return {'kind':'generic_food','food':food,'grams':chosen,'unit':correct_unit,
            'nutrition':nutrients(food,chosen) if chosen is not None else None,
            'auto_logged':False,'needs_confirmation':True,
            'quantity_method':'user_specified' if amount else ('typical_piece_assumption' if count_match else 'unquantified'),
            'warning':'Nutrition values are illustrative; confirm portion and source before logging.'}

def parse_meal_text(text):
    """Split explicit conjunctions/commas; no guess about cooking quantities.
    Each component must still be confirmed before logging.
    """
    if len(text)>500:raise ValueError('Text must be at most 500 characters')
    parts=[p.strip() for p in re.split(r'\s*[,;+]\s*|\s+and\s+',text,flags=re.I) if p.strip()]
    if not 1<=len(parts)<=12:raise ValueError('Enter up to 12 distinct items')
    items=[parse_entry(p) for p in parts]
    return {'items':items,'ready_to_log':False,'requires_review':True,
            'message':'Confirm each dish, product variant, source and serving before logging.'}
