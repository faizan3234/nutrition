"""Reliv Nutrition AI prototype. Self-hosted API with optional vision providers."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import uuid
from fastapi import FastAPI,HTTPException,Query,Request
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .catalog import FOODS, LOOKUP, search_foods, nutrients, serving_unit
from .db import connection,init_db
from .personalization import initialize as initialize_personalization, save_plate, get_plate, add_shortcut, list_shortcuts, shortcut_meal
from .quality import nutrition_quality
from .vision import analyze
from .packaged import lookup_barcode, search_products, scaled_product
from .restaurants import search_restaurants, estimate_restaurant
from .textlog import parse_entry
from .recipes import calculate_recipe
from .usda import search_usda, lookup_usda
from .auth import authorized_profile
from .learning import (initialize as initialize_learning,authorize_admin,create_examples,list_examples,review_sample,
    create_feedback,list_feedback,review_feedback,statistics,export_manifest,get_approved_food,
    revoke_sample,feedback_photo_path)

BASE=Path(__file__).resolve().parent.parent
app=FastAPI(title='Reliv Nutrition AI',version='0.6.0',description='Camera-ready prototype with explicit uncertainty and configurable vision')
origins=[x.strip() for x in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if x.strip()]
if origins:
    app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','Authorization'])
init_db()
initialize_learning()
initialize_personalization()
app.mount('/admin/assets',StaticFiles(directory=BASE/'admin'),name='admin_assets')
app.mount('/assets',StaticFiles(directory=BASE/'web'),name='assets')
@app.get('/sw.js',include_in_schema=False)
def service_worker():
    return FileResponse(BASE/'web'/'sw.js',media_type='application/javascript',headers={'Service-Worker-Allowed':'/'})

class PhotoRequest(BaseModel):
    image_base64:str=Field(min_length=100,max_length=10_500_000)
    secondary_image_base64:str|None=Field(default=None,max_length=10_500_000)
    plate_diameter_cm:float|None=Field(default=None,ge=10,le=40)
def eaten_amount(served_amount: float, consumed_percent: float) -> float:
    """Persist eaten, not offered mass. The option does NOT improve photo weighing accuracy."""
    from decimal import Decimal, ROUND_HALF_UP
    return float((Decimal(str(served_amount)) * Decimal(str(consumed_percent)) / Decimal('100'))
                 .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

class LogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    food_id:str
    grams:float=Field(gt=0,le=5000) # presented/served amount
    consumed_percent:float=Field(default=100,gt=0,le=100)
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')
class ProductLogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    barcode:str=Field(pattern=r'^\d{8,14}$')
    amount:float=Field(gt=0,le=5000)
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')
class BatchItem(BaseModel):
    food_id:str
    grams:float=Field(gt=0,le=5000) # presented/served amount
    consumed_percent:float=Field(default=100,gt=0,le=100)
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')
class BatchLogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    items:list[BatchItem]=Field(min_length=1,max_length=12)

class TotalsRequest(BaseModel):pass

@app.get('/')
def index():return FileResponse(BASE/'web'/'index.html')
@app.get('/admin',include_in_schema=False)
def admin_page():return FileResponse(BASE/'admin'/'index.html')

@app.get('/api/health')
def health():return {'ok':True,'catalog_size':len(FOODS),'status':'prototype'}

@app.get('/api/model-info')
def get_model_info():
    from .vision import model_info
    return model_info()

@app.get('/api/coverage')
def coverage():
    from collections import Counter
    from .legacy_adapters import KNOWN_22_LABELS
    return {'searchable_foods':len(FOODS), 'by_category':dict(sorted(Counter(f['category'] for f in FOODS).items())),
            'indian_22_model_labels':KNOWN_22_LABELS,
            'recognition_accuracy_catalog':None,'portion_accuracy_catalog':None,
            'recognition_accuracy_on_171':None,'portion_accuracy_on_171':None, # legacy API field names (deprecated)

            'note':'Search coverage is NOT camera recognition coverage. Nutrition starter values are not validated.'}
@app.get('/api/foods')
def foods(q:str='',limit:int=Query(40,ge=1,le=250)):
    return {'items':[{**f,'nutrition_quality':nutrition_quality(f['source'])} for f in search_foods(q,limit)],'catalog_status':'illustrative_values_not_authoritative'}
@app.get('/api/products/search')
def product_search(q:str=Query(min_length=2,max_length=100)):
    try:return {'items':search_products(q),'source':'Open Food Facts (ODbL)', 'live':True}
    except RuntimeError as exc:raise HTTPException(status_code=503,detail=str(exc))

@app.get('/api/products/barcode/{barcode}')
def product_lookup(barcode:str):
    try:return lookup_barcode(barcode)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc))
    except LookupError as exc:raise HTTPException(status_code=404,detail=str(exc))
    except RuntimeError as exc:raise HTTPException(status_code=503,detail=str(exc))

@app.post('/api/products/log',status_code=201)
def log_product(req:ProductLogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:p=lookup_barcode(req.barcode)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc))
    except LookupError as exc:raise HTTPException(status_code=404,detail=str(exc))
    except RuntimeError as exc:raise HTTPException(status_code=503,detail=str(exc))
    if not p['complete']:
        raise HTTPException(status_code=422,detail='Product nutrition label incomplete; use verified packaging')
    nutrition=scaled_product(p,req.amount)
    rec={'id':str(uuid.uuid4()),'profile':req.profile,'food_id':'off:'+p['barcode'],
         'food_name':(p['brand']+' '+p['name']).strip(),'grams':req.amount,
         'unit':p['unit'], 'source':p['source'], 'meal':req.meal,
         **nutrition,'created_at':datetime.now(timezone.utc).isoformat()}
    with connection() as c:
        c.execute('''INSERT INTO meal_logs
            (id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',tuple(rec[k] for k in
            ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source')))
    return rec

@app.post('/api/analyze')
def photo(req:PhotoRequest):
    try:return analyze(req.image_base64,req.secondary_image_base64,req.plate_diameter_cm)
    except ValueError as e:raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        # Never expose server secrets or third-party responses.
        raise HTTPException(status_code=503,detail=f'Vision unavailable: {type(e).__name__}')
@app.post('/api/log',status_code=201)
def log(req:LogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    f=LOOKUP.get(req.food_id) or get_approved_food(req.food_id)
    if not f:raise HTTPException(status_code=404,detail='Unknown food')
    consumed=eaten_amount(req.grams,req.consumed_percent)
    nutrition=nutrients(f,consumed)
    rec={'id':str(uuid.uuid4()),'profile':req.profile,'food_id':f['id'],'food_name':f['name'],
         'grams':consumed,'served_amount':req.grams,'consumed_percent':req.consumed_percent,
         'unit':serving_unit(f),'source':f['source'],'nutrition_quality':nutrition_quality(f['source']),'meal':req.meal,**nutrition,'created_at':datetime.now(timezone.utc).isoformat()}
    with connection() as c:
        c.execute("""INSERT INTO meal_logs (id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source,served_amount,consumed_percent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  tuple(rec[k] for k in ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source','served_amount','consumed_percent')))
    return rec
@app.post('/api/log/batch',status_code=201)
def batch_log(req:BatchLogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    entries=[]
    # Validate all rows before committing anything.
    for item in req.items:
        f=LOOKUP.get(item.food_id) or get_approved_food(item.food_id)
        if not f:raise HTTPException(status_code=404,detail='Unknown food: '+item.food_id)
        eaten=eaten_amount(item.grams,item.consumed_percent)
        entries.append({'id':str(uuid.uuid4()),'profile':req.profile,'food_id':f['id'],
             'food_name':f['name'],'grams':eaten,'served_amount':item.grams,
             'consumed_percent':item.consumed_percent,'meal':item.meal,
             'unit':serving_unit(f),'source':f['source'],'nutrition_quality':nutrition_quality(f['source']),
             **nutrients(f,eaten),'created_at':datetime.now(timezone.utc).isoformat()})
    with connection() as c:
        c.executemany('''INSERT INTO meal_logs
            (id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source,served_amount,consumed_percent)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', [tuple(r[k] for k in
            ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source','served_amount','consumed_percent')) for r in entries])
    return {'count':len(entries),'items':entries,
            'totals':{k:round(sum(r[k] for r in entries),1) for k in ('kcal','protein','carbs','fat')}}

@app.get('/api/day')
def day(request:Request,profile:str=Query(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$'),date:str=Query(pattern=r'^\d{4}-\d{2}-\d{2}$'),offset_minutes:int=Query(0,ge=-840,le=840)):
    authorized_profile(request.headers,profile)
    # JavaScript getTimezoneOffset() is minutes added to local time to obtain UTC.
    # Convert UTC timestamps to user's offset before comparing the calendar date.
    with connection() as c:
        rows=c.execute('SELECT * FROM meal_logs WHERE profile=? ORDER BY created_at DESC',(profile,)).fetchall()
    items=[dict(r) for r in rows if (datetime.fromisoformat(r['created_at'])-timedelta(minutes=offset_minutes)).date().isoformat()==date]
    totals={k:round(sum(item[k] for item in items),1) for k in ('kcal','protein','carbs','fat')}
    return {'date':date,'items':items,'totals':totals,'note':'Day grouping uses browser-provided UTC offset.'}
@app.delete('/api/log/{log_id}',status_code=200)
def delete(log_id:str,request:Request,profile:str=Query(min_length=8,max_length=100)):
    authorized_profile(request.headers,profile)
    with connection() as c:
        count=c.execute('DELETE FROM meal_logs WHERE id=? AND profile=?',(log_id,profile)).rowcount
    if not count:raise HTTPException(status_code=404,detail='Not found')
    return {'deleted':True}

# Sourced restaurant menus never imply verified restaurant nutrition.
class RestaurantEstimate(BaseModel):
    brand:str=Field(min_length=2,max_length=90)
    dish:str=Field(min_length=2,max_length=150)
    grams:float=Field(gt=0,le=5000)
    use_generic_estimate:bool=False

@app.get('/api/restaurants')
def restaurant_search(q:str=Query(min_length=2,max_length=100)):
    return {'items':search_restaurants(q),'note':'Official menu is not a nutrition facts table.'}

@app.post('/api/restaurants/estimate')
def restaurant_estimate(req:RestaurantEstimate):
    try:return estimate_restaurant(req.brand,req.dish,req.grams,req.use_generic_estimate)
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(422,str(e))

class TextEntry(BaseModel):
    text:str=Field(min_length=1,max_length=250)

@app.post('/api/parse-text')
def parse_text(req:TextEntry):
    try:return parse_entry(req.text)
    except ValueError as e:raise HTTPException(422,str(e))

class RecipeIngredient(BaseModel):
    food_id:str|None=None
    grams:float=Field(gt=0,le=15000)
    name:str|None=None
    per100:dict[str,float]|None=None
    role:str='ingredient'
    preparation:str='as_served'
    source_note:str|None=None
class RecipeRequest(BaseModel):
    ingredients:list[RecipeIngredient]=Field(min_length=1,max_length=50)
    cooked_yield_g:float|None=Field(None,gt=0,le=100000)

@app.post('/api/recipes/estimate')
def recipe_estimate(req:RecipeRequest):
    try:return calculate_recipe([x.model_dump() for x in req.ingredients],req.cooked_yield_g)
    except ValueError as e:raise HTTPException(422,str(e))

@app.get('/api/readiness')
def readiness():
    from .vision import model_info
    info=model_info()
    failed=['real_photo_recognition_benchmark','real_image_detection_map','weighed_food_portion_benchmark',
            'validated_nutrition_data_for_all_recipes','authenticated_user_access','independent_commercial_comparison',
            'real_mobile_device_camera_qa','security_review']
    return {'production_ready':False,'model_ready':info['ready'],'blocking_gates':failed,
       'marketing_claim':'Do not claim most accurate, exact calories or production validated',
       'catalog_count':len(FOODS)}

@app.post('/api/parse-meal')
def parse_meal(req:TextEntry):
    from .textlog import parse_meal_text
    try:return parse_meal_text(req.text)
    except ValueError as e:raise HTTPException(422,str(e))

class RestaurantLogRequest(RestaurantEstimate):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')

@app.post('/api/restaurants/log',status_code=201)
def restaurant_log(req:RestaurantLogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:est=estimate_restaurant(req.brand,req.dish,req.grams,req.use_generic_estimate)
    except LookupError as e:raise HTTPException(404,str(e))
    except ValueError as e:raise HTTPException(422,str(e))
    if not est.get('nutrition'):
        raise HTTPException(422,'Restaurant nutrition unavailable. Explicitly confirm generic recipe estimate or supply audited source.')
    n=est['nutrition'];rec={'id':str(uuid.uuid4()),'profile':req.profile,
         'food_id':'restaurant:'+req.brand.casefold().replace(' ','-')+':'+req.dish.casefold().replace(' ','-'),
         'food_name':req.brand+' — '+req.dish,'grams':req.grams,'unit':'g',
         'source':est['source']+' / '+(est.get('evidence_url') or ''),'meal':req.meal,
         **n,'created_at':datetime.now(timezone.utc).isoformat()}
    with connection() as c:
        c.execute('''INSERT INTO meal_logs (id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',tuple(rec[k] for k in
                  ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source')))
    return {**rec,'restaurant_specific_nutrition':est['is_restaurant_specific'],
            'warning':est.get('warning') or 'Check serving portion and source.'}

@app.get('/api/reference-foods')
def usda_search(q:str=Query(min_length=2,max_length=100)):
    try:return {'items':search_usda(q),'source':'USDA FoodData Central (CC0)',
                'warning':'Select the correct cooked/raw/preparation record.'}
    except RuntimeError as e:raise HTTPException(503,str(e))
    except ValueError as e:raise HTTPException(422,str(e))

class ReferenceLogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    fdc_id:int=Field(gt=0,le=1000000000)
    grams:float=Field(gt=0,le=5000)
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')

@app.post('/api/reference-foods/log',status_code=201)
def reference_log(req:ReferenceLogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:entry=lookup_usda(req.fdc_id)
    except ValueError as e:raise HTTPException(422,str(e))
    except LookupError as e:raise HTTPException(404,str(e))
    except RuntimeError as e:raise HTTPException(503,str(e))
    from decimal import Decimal,ROUND_HALF_UP
    def scale(x):return float((Decimal(str(x))*Decimal(str(req.grams))/100).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))
    rec={'id':str(uuid.uuid4()),'profile':req.profile,
         'food_id':'usda:'+str(req.fdc_id),'food_name':entry['name'],'grams':req.grams,'unit':'g',
         'source':entry['source']+' '+entry['source_url'],'meal':req.meal,
         **{k:scale(v) for k,v in entry['per_100g'].items()},
         'created_at':datetime.now(timezone.utc).isoformat()}
    with connection() as c:
        c.execute('INSERT INTO meal_logs (id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',tuple(rec[k] for k in
                  ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source')))
    return rec


# Human-in-the-loop learning, with dedicated protected admin endpoints.
class AdminFoodItem(BaseModel):
    name:str=Field(min_length=2,max_length=120)
    recipe_variant:str=''
    grams:float=Field(gt=0,le=5000)
    kcal:float=Field(ge=0,le=5000)
    protein:float=Field(ge=0,le=500)
    carbs:float=Field(ge=0,le=500)
    fat:float=Field(ge=0,le=500)
    source_kind:str
    weight_basis:str='estimated'
    nutrient_basis:str='per_100g'
    evidence_url:str=''
    note:str=''
    bbox:list[float]|None=None
class AdminAddRequest(BaseModel):
    image_base64:str=Field(min_length=100,max_length=10_500_000)
    photo_group:str=Field(min_length=3,max_length=100)
    plate_diameter_cm:float|None=Field(default=None,ge=10,le=40)
    photo_use_rights_confirmed:bool=False
    items:list[AdminFoodItem]=Field(min_length=1,max_length=12)

@app.get('/api/admin/learning/stats')
def admin_learning_stats(request:Request):
    authorize_admin(request.headers)
    return statistics()

@app.post('/api/admin/learning/examples',status_code=201)
def admin_add_examples(req:AdminAddRequest,request:Request):
    authorize_admin(request.headers)
    try:return create_examples(req.image_base64,[i.model_dump() for i in req.items],req.photo_group,req.plate_diameter_cm,req.photo_use_rights_confirmed)
    except ValueError as exc:raise HTTPException(422,str(exc))

class AdminRevokeRequest(BaseModel):
    reason:str=Field(min_length=8,max_length=400)

@app.post('/api/admin/learning/examples/{example_id}/revoke')
def admin_revoke_example(example_id:str,req:AdminRevokeRequest,request:Request):
    authorize_admin(request.headers)
    try:return revoke_sample(example_id,req.reason)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except LookupError as exc:raise HTTPException(404,str(exc))

@app.get('/api/admin/learning/examples')
def admin_get_examples(request:Request,status:str='pending'):
    authorize_admin(request.headers)
    try:return {'items':list_examples(status)}
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.post('/api/admin/learning/examples/{example_id}/{decision}')
def admin_review_examples(example_id:str,decision:str,request:Request):
    authorize_admin(request.headers)
    try:return review_sample(example_id,decision)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except LookupError as exc:raise HTTPException(404,str(exc))

class FoodFeedbackRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    reference_id:str|None=None
    corrected_name:str=Field(min_length=2,max_length=120)
    corrected_grams:float|None=Field(None,gt=0,le=5000)
    comment:str=Field(default='',max_length=500)
    consent_to_admin_review:bool=False
    consent_to_reference_training:bool=False
    image_base64:str|None=Field(default=None,max_length=10_500_000)

@app.post('/api/learning/feedback',status_code=201)
def user_learning_feedback(req:FoodFeedbackRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:return create_feedback(req.profile,req.corrected_name,req.corrected_grams,req.comment,
                          req.reference_id,req.consent_to_admin_review,req.image_base64,req.consent_to_reference_training)
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.get('/api/admin/learning/feedback/{feedback_id}/photo')
def admin_feedback_photo(feedback_id:str,request:Request):
    authorize_admin(request.headers)
    try:p=feedback_photo_path(feedback_id)
    except LookupError as exc:raise HTTPException(404,str(exc))
    return FileResponse(p,media_type='image/jpeg',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@app.get('/api/admin/learning/feedback')
def admin_get_feedback(request:Request,status:str='pending'):
    authorize_admin(request.headers)
    try:return {'items':list_feedback(status)}
    except ValueError as exc:raise HTTPException(422,str(exc))

@app.post('/api/admin/learning/feedback/{feedback_id}/{decision}')
def admin_feedback_decide(feedback_id:str,decision:str,request:Request):
    authorize_admin(request.headers)
    try:return review_feedback(feedback_id,decision)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except LookupError as exc:raise HTTPException(404,str(exc))

@app.get('/api/admin/learning/export')
def admin_export(request:Request):
    authorize_admin(request.headers)
    return {'items':export_manifest(),
            'warning':'Private image paths, not downloadable images. Export only for authorized offline training; enforce split boundaries.'}

@app.get('/api/admin/learning/validation')
def admin_validation(request:Request):
    authorize_admin(request.headers)
    from .learning import validation_gates
    return validation_gates()

# Continued master project: user features stay independent from admin learning.
class PlateProfileRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    diameter_cm:float=Field(ge=10,le=40)
    label:str=Field(default='My plate',min_length=2,max_length=60)

@app.put('/api/me/plate')
def set_plate(req:PlateProfileRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    return save_plate(req.profile,req.diameter_cm,req.label)

@app.get('/api/me/plate')
def user_plate(request:Request,profile:str=Query(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')):
    authorized_profile(request.headers,profile)
    return {'plate':get_plate(profile)}

class ShortcutRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    food_id:str=Field(min_length=2,max_length=150)
    serving_amount:float=Field(gt=0,le=5000)
    nickname:str=Field(min_length=2,max_length=80)

@app.post('/api/me/shortcuts',status_code=201)
def create_shortcut(req:ShortcutRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:return add_shortcut(req.profile,req.food_id,req.serving_amount,req.nickname)
    except LookupError as exc:raise HTTPException(404,str(exc))

@app.get('/api/me/shortcuts')
def get_shortcuts(request:Request,profile:str=Query(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')):
    authorized_profile(request.headers,profile)
    return {'items':list_shortcuts(profile)}

class ShortcutLogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    fraction:float=Field(default=1,gt=0,le=10)
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')

@app.post('/api/me/shortcuts/{shortcut_id}/log',status_code=201)
def log_shortcut(shortcut_id:str,req:ShortcutLogRequest,request:Request):
    authorized_profile(request.headers,req.profile)
    try:result=shortcut_meal(req.profile,shortcut_id,req.fraction,req.meal)
    except LookupError as exc:raise HTTPException(404,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))
    rec={'id':str(uuid.uuid4()),'profile':req.profile,**result,
         'created_at':datetime.now(timezone.utc).isoformat(),
         'nutrition_quality':nutrition_quality(result['source'])}
    with connection() as db:
        db.execute('INSERT INTO meal_logs(id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source,served_amount,consumed_percent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
          tuple(rec[k] for k in ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source'))+(rec['grams'],100))
    return rec

class LabelReadRequest(BaseModel):
    image_base64:str=Field(min_length=100,max_length=10_500_000)

@app.post('/api/products/label/read')
def read_product_label(req:LabelReadRequest):
    from .label_reader import read_label
    try:return read_label(req.image_base64)
    except ValueError as exc:raise HTTPException(422,str(exc))
    except RuntimeError as exc:raise HTTPException(503,str(exc))
    except Exception as exc:raise HTTPException(503,'Nutrition label reading unavailable') from exc

class LabelLogRequest(BaseModel):
    profile:str=Field(min_length=8,max_length=100,pattern=r'^[a-zA-Z0-9_-]+$')
    brand:str=Field(min_length=1,max_length=80)
    name:str=Field(min_length=2,max_length=120)
    amount:float=Field(gt=0,le=5000)
    unit:str=Field(pattern=r'^(g|ml)$')
    per_100:dict[str,float]
    meal:str=Field(pattern=r'^(Breakfast|Lunch|Dinner|Snacks)$')
    label_verified_by_user:bool=False

@app.post('/api/products/label/log',status_code=201)
def log_manual_label(req:LabelLogRequest,request:Request):
    from decimal import Decimal,ROUND_HALF_UP
    from math import isfinite
    authorized_profile(request.headers,req.profile)
    if not req.label_verified_by_user:raise HTTPException(422,'Check package and confirm all four nutrition values')
    if set(req.per_100)!={'kcal','protein','carbs','fat'}:
        raise HTTPException(422,'Label needs kcal, protein, carbs and fat per 100g or 100ml')
    if any(not isfinite(v) or v<0 or v>(1000 if k=='kcal' else 100) for k,v in req.per_100.items()):
        raise HTTPException(422,'Label nutrients outside plausible range')
    nutrition={k:float((Decimal(str(v))*Decimal(str(req.amount))/100).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)) for k,v in req.per_100.items()}
    rec={'id':str(uuid.uuid4()),'profile':req.profile,'food_id':'user-label:'+str(uuid.uuid4()),
       'food_name':req.brand.strip()+' '+req.name.strip(),'grams':req.amount,'unit':req.unit,
       'meal':req.meal,'source':'user_label_unverified',**nutrition,
       'created_at':datetime.now(timezone.utc).isoformat(),
       'nutrition_quality':nutrition_quality('user_label_unverified')}
    with connection() as db:
        db.execute('INSERT INTO meal_logs(id,profile,food_id,food_name,grams,meal,kcal,protein,carbs,fat,created_at,unit,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
          tuple(rec[k] for k in ('id','profile','food_id','food_name','grams','meal','kcal','protein','carbs','fat','created_at','unit','source')))
    return rec

class GroqProductSearchRequest(BaseModel):
    query:str=Field(min_length=2,max_length=150)

@app.post('/api/groq/product-search')
def groq_product_search(req:GroqProductSearchRequest):
    from .groq_service import search_packaged_nutrition
    try:
        return search_packaged_nutrition(req.query)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    except RuntimeError as exc:
        raise HTTPException(503,str(exc))

class GroqVoiceRequest(BaseModel):
    audio_base64:str=Field(min_length=10)
    filename:str='voice.webm'

@app.post('/api/groq/transcribe')
def groq_transcribe(req:GroqVoiceRequest):
    import base64
    from .groq_service import transcribe_audio
    raw_b64 = req.audio_base64.split(',', 1)[1] if ',' in req.audio_base64 else req.audio_base64
    try:
        raw_bytes = base64.b64decode(raw_b64, validate=True)
    except Exception as exc:
        raise HTTPException(400, 'Invalid base64 audio data')
    try:
        text = transcribe_audio(raw_bytes, req.filename)
        return {'text': text}
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))

class GroqKeyRequest(BaseModel):
    key:str=Field(min_length=10,max_length=150)

@app.post('/api/settings/groq-key')
def set_groq_key(req:GroqKeyRequest):
    import re
    clean_key = req.key.strip()
    if not clean_key.startswith('gsk_'):
        raise HTTPException(400, 'Invalid Groq API key format (should start with gsk_)')
    os.environ['GROQ_API_KEY'] = clean_key
    env_path = BASE / '.env'
    if env_path.is_file():
        try:
            content = env_path.read_text(encoding='utf-8')
            if 'GROQ_API_KEY=' in content:
                new_content = re.sub(r'GROQ_API_KEY=.*', f'GROQ_API_KEY={clean_key}', content)
            else:
                new_content = content + f'\nGROQ_API_KEY={clean_key}\n'
            env_path.write_text(new_content, encoding='utf-8')
        except OSError:
            pass  # Read-only filesystem in serverless environments like Vercel
    return {'ok': True, 'message': 'Groq API key saved! Camera food recognition is now active.'}

@app.get('/api/admin/learning/triage')
def admin_triage(request:Request):
    authorize_admin(request.headers)
    from .learning_monitor import triage
    return triage()

class EvaluationRequest(BaseModel):
    rows:list[dict]=Field(min_length=1,max_length=10000)

@app.post('/api/admin/evaluate/heldout')
def admin_heldout(req:EvaluationRequest,request:Request):
    authorize_admin(request.headers)
    from .evaluation_monitor import summarize
    try:return summarize(req.rows)
    except ValueError as exc:raise HTTPException(422,str(exc))
