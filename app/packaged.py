"""Verified-on-demand product lookup using Open Food Facts (ODbL).

Products are not represented as AI guesses. A product is only loggable when the
remote record contains energy, protein, carbohydrate and fat per 100 g/ml.
Open Food Facts is community supplied: source attribution is mandatory and
users should compare the photographed package's nutrition label.
"""
from __future__ import annotations
from functools import lru_cache
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://world.openfoodfacts.org'
FIELDS = 'code,product_name,product_name_en,brands,nutriments,quantity,serving_size,nutrition_data_per,product_quantity_unit,categories_tags'


def _read(url: str):
    req = urllib.request.Request(url, headers={
        'User-Agent': os.getenv('OFF_USER_AGENT',
            'RelivNutritionAI/0.5 (https://relivkiosk.vercel.app)'),
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            if res.status != 200:
                raise RuntimeError('Product database unavailable')
            return json.load(res)
    except (TimeoutError, OSError, urllib.error.URLError, ValueError) as exc:
        raise RuntimeError('Product database unavailable; try barcode or manual food entry') from exc


def _numeric(value, maximum):
    # bool is a subclass of int but must not be accepted as numeric.
    if isinstance(value, bool): return None
    try: n = float(value)
    except (TypeError, ValueError, OverflowError): return None
    return round(n, 3) if math.isfinite(n) and 0 <= n <= maximum else None


def normalize_product(product: dict, code: str | None = None):
    if not isinstance(product, dict): return None
    code = str(code or product.get('code') or '')
    if not re.fullmatch(r'\d{8,14}', code): return None
    n = product.get('nutriments') or {}
    if not isinstance(n, dict): return None
    calories = _numeric(n.get('energy-kcal_100g'), 950)
    if calories is None:
        kj = _numeric(n.get('energy-kj_100g'), 4200)
        calories = round(kj / 4.184, 2) if kj is not None else None
    protein = _numeric(n.get('proteins_100g'), 100)
    carbs = _numeric(n.get('carbohydrates_100g'), 100)
    fat = _numeric(n.get('fat_100g'), 100)
    missing = [name for name, value in [('calories', calories), ('protein', protein),
                                        ('carbohydrates', carbs), ('fat', fat)] if value is None]
    name = str(product.get('product_name_en') or product.get('product_name') or '').strip()[:160]
    if not name: return None
    brand = str(product.get('brands') or '').strip()[:100]
    raw_unit = str(product.get('product_quantity_unit') or '').lower()
    serving = str(product.get('serving_size') or '').lower()
    raw_qty = str(product.get('quantity') or '').lower()
    # For products sold by volume OFF's _100g nutrient fields are normalized per
    # 100 mL. Only show ml if volume units are explicitly present in metadata.
    unit = 'ml' if raw_unit in ('ml','cl','l') or (not raw_unit and re.search(r'\b\d+(?:\.\d+)?\s*(ml|cl|litre|liter|l)\b',serving+' '+raw_qty)) else 'g'
    return {'barcode': code, 'name': name, 'brand': brand, 'unit': unit,
            'kcal': calories, 'protein': protein, 'carbs': carbs, 'fat': fat,
            'complete': not missing, 'missing': missing,
            'source': 'Open Food Facts community product record (ODbL)',
            'source_url': f'{BASE}/product/{code}',
            'nutrition_basis': 'per 100 '+unit,
            'confidence_warning': 'Community-entered label: verify against actual packaging and product variant.'}


@lru_cache(maxsize=500)
def lookup_barcode(code: str):
    if not re.fullmatch(r'\d{8,14}', code): raise ValueError('Barcode must contain 8–14 digits')
    url = f'{BASE}/api/v3/product/{code}?'+urllib.parse.urlencode({'fields':FIELDS})
    data = _read(url)
    product = data.get('product') or {}
    # v3 not-found response differs from v2; fail closed when no product name.
    result = normalize_product(product, code)
    if result is None: raise LookupError('Product or nutrition label not found')
    return result


def search_products(query: str, limit=12):
    q = query.strip()
    if len(q) < 2 or len(q) > 100: raise ValueError('Search must be 2–100 characters')
    # Search-a-licious is evolving. This documented legacy search supports
    # product-name keyword search; barcode lookups use current v3.
    url = f'{BASE}/cgi/search.pl?' + urllib.parse.urlencode({
        'search_terms':q, 'search_simple':1, 'action':'process', 'json':1,
        'page_size':min(limit,20), 'fields':FIELDS,
    })
    payload = _read(url)
    results=[]
    for obj in (payload.get('products') or [])[:40]:
        normalized=normalize_product(obj)
        if normalized: results.append(normalized)
        if len(results)>=limit: break
    return results


def scaled_product(product: dict, amount: float):
    if not product.get('complete'):raise ValueError('Incomplete nutrition label: cannot calculate')
    from decimal import Decimal, ROUND_HALF_UP
    if not 0 < amount <= 5000: raise ValueError('Invalid quantity')
    return {k:float((Decimal(str(product[k]))*Decimal(str(amount))/Decimal(100)).quantize(
        Decimal('0.1'), rounding=ROUND_HALF_UP)) for k in ('kcal','protein','carbs','fat')}
