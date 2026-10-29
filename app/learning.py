"""Admin-curated food examples and cautious similarity retrieval.

A reviewed example is a reference, NOT proof of photo weighing accuracy.
Same-image examples may restore an admin-recorded serving; perceptual neighbors
must not inherit serving weight or nutrients without explicit user confirmation.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
from .db import connection
from .vision import normalize_image

DATA_DIR = Path(os.getenv('RELIV_LEARNING_IMAGE_DIR', './private_learning_images'))
SOURCES = {'weighed_recipe', 'packaged_label', 'official_database', 'laboratory', 'estimated_recipe'}
NUMERIC = ('kcal', 'protein', 'carbs', 'fat')


def now():
    return datetime.now(timezone.utc).isoformat()


def authorize_admin(headers):
    token = os.getenv('RELIV_ADMIN_TOKEN', '')
    if len(token) < 32:
        raise HTTPException(503, 'Admin access disabled until RELIV_ADMIN_TOKEN is configured (32+ chars)')
    supplied = headers.get('authorization', '')
    if not supplied.startswith('Bearer ') or not secrets.compare_digest(supplied[7:], token):
        raise HTTPException(401, 'Valid admin bearer token required')


def initialize():
    with connection() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS learning_photos (
            id TEXT PRIMARY KEY, image_sha TEXT NOT NULL, dhash TEXT NOT NULL,
            image_path TEXT NOT NULL, photo_group TEXT NOT NULL,
            dataset_split TEXT NOT NULL, created_at TEXT NOT NULL,
            plate_diameter_cm REAL, rights_attested INTEGER NOT NULL DEFAULT 0)''')
        photo_columns={r['name'] for r in c.execute('PRAGMA table_info(learning_photos)')}
        if 'plate_diameter_cm' not in photo_columns:
            c.execute('ALTER TABLE learning_photos ADD COLUMN plate_diameter_cm REAL')
        if 'rights_attested' not in photo_columns:
            c.execute('ALTER TABLE learning_photos ADD COLUMN rights_attested INTEGER NOT NULL DEFAULT 0')
        c.execute('CREATE INDEX IF NOT EXISTS learning_photos_sha ON learning_photos(image_sha)')
        c.execute('''CREATE TABLE IF NOT EXISTS learning_examples (
            id TEXT PRIMARY KEY, photo_id TEXT NOT NULL,
            name TEXT NOT NULL, recipe_variant TEXT NOT NULL,
            grams REAL NOT NULL, unit TEXT NOT NULL,
            kcal REAL NOT NULL, protein REAL NOT NULL, carbs REAL NOT NULL, fat REAL NOT NULL,
            source_kind TEXT NOT NULL, evidence_url TEXT NOT NULL,
            note TEXT NOT NULL, bbox_json TEXT,
            status TEXT NOT NULL, approved_at TEXT, created_at TEXT NOT NULL,
            input_basis TEXT NOT NULL DEFAULT 'per_100g',
            weight_basis TEXT NOT NULL DEFAULT 'estimated',
            FOREIGN KEY(photo_id) REFERENCES learning_photos(id))''')
        existing={r['name'] for r in c.execute('PRAGMA table_info(learning_examples)')}
        if 'input_basis' not in existing:
            c.execute("ALTER TABLE learning_examples ADD COLUMN input_basis TEXT NOT NULL DEFAULT 'per_100g'")
        if 'weight_basis' not in existing:
            c.execute("ALTER TABLE learning_examples ADD COLUMN weight_basis TEXT NOT NULL DEFAULT 'estimated'")
        c.execute('CREATE INDEX IF NOT EXISTS learning_examples_status ON learning_examples(status)')
        c.execute('''CREATE TABLE IF NOT EXISTS learning_embeddings (
            photo_id TEXT NOT NULL, model_key TEXT NOT NULL, vector_json TEXT NOT NULL,
            indexed_at TEXT NOT NULL, PRIMARY KEY(photo_id,model_key))''')
        c.execute('''CREATE TABLE IF NOT EXISTS learning_feedback (
            id TEXT PRIMARY KEY, profile TEXT NOT NULL, reference_id TEXT,
            corrected_name TEXT NOT NULL, corrected_grams REAL,
            comment TEXT NOT NULL, image_path TEXT,
            consent INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            training_consent INTEGER NOT NULL DEFAULT 0)''')
        fbcols={r['name'] for r in c.execute('PRAGMA table_info(learning_feedback)')}
        if 'training_consent' not in fbcols:
            c.execute('ALTER TABLE learning_feedback ADD COLUMN training_consent INTEGER NOT NULL DEFAULT 0')


def dhash(image_bytes: bytes) -> str:
    with Image.open(io.BytesIO(image_bytes)) as im:
        # Cheap similarity search for near-identical framing. Not a semantic food model.
        small = im.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
        px = list(small.get_flattened_data()) if hasattr(small, "get_flattened_data") else list(small.getdata())
    code = 0
    for y in range(8):
        for x in range(8):
            code = (code << 1) | (1 if px[y * 9 + x] > px[y * 9 + x + 1] else 0)
    return f'{code:016x}'


def group_split(group: str) -> str:
    key = int(hashlib.sha256(group.encode('utf-8')).hexdigest()[:8], 16) % 100
    return 'train' if key < 80 else ('validation' if key < 90 else 'test')


def safe_photo_path(photo_id: str) -> Path:
    return DATA_DIR / f'{photo_id}.jpg'


def persist_photo(image_bytes: bytes, prefix: str = 'example') -> tuple[str, str]:
    photo_id = str(uuid.uuid4())
    DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = safe_photo_path(photo_id)
    # No user-provided filenames; keep scans out of publicly served /assets.
    with path.open('xb') as output:
        os.chmod(path, 0o600)
        output.write(image_bytes)
    return photo_id, str(path)


def validate_items(items: list[dict]):
    if not 1 <= len(items) <= 12:
        raise ValueError('Supply 1-12 labeled food items per photo')
    for item in items:
        name = str(item.get('name', '')).strip()
        if len(name) < 2 or len(name) > 120:
            raise ValueError('Each item needs a 2-120 character food name')
        amount = item.get('grams')
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or not 1 <= amount <= 5000:
            raise ValueError('Admin must enter independently weighed or recorded edible weight (1-5000g)')
        kind = item.get('source_kind')
        if kind not in SOURCES:
            raise ValueError('Nutrition source must be explicitly classified')
        weight_basis=item.get('weight_basis','estimated')
        if weight_basis not in ('scale','packaging','estimated'):
            raise ValueError('weight_basis must be scale, packaging or estimated')
        basis = item.get('nutrient_basis','per_100g')
        if basis not in ('per_100g','total_for_weighed_portion'):
            raise ValueError('Nutrition basis must be per_100g or total_for_weighed_portion')
        for nutrient in NUMERIC:
            value = item.get(nutrient)
            normalized = (value * 100 / amount) if isinstance(value,(int,float)) and basis == 'total_for_weighed_portion' else value
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not isinstance(normalized,(int,float)) or not math.isfinite(normalized) or not 0 <= normalized <= (1000 if nutrient == 'kcal' else 100):
                raise ValueError('Nutrition must normalize to plausible finite per-100g values')
        bbox = item.get('bbox')
        if bbox is not None:
            if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in bbox):
                raise ValueError('bbox must be four normalized [x1,y1,x2,y2] coordinates')
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                raise ValueError('Invalid annotation rectangle')
        evidence = str(item.get('evidence_url') or '').strip()
        if evidence and (not evidence.startswith('https://') or len(evidence) > 600):
            raise ValueError('Evidence must be a short HTTPS link')
        note = str(item.get('note') or '')
        if len(note) > 1000 or len(str(item.get('recipe_variant') or '')) > 150:
            raise ValueError('Note or recipe variant too long')
        if kind in {'weighed_recipe','laboratory','packaged_label','official_database'} and not evidence and len(note.strip()) < 15:
            raise ValueError('Non-estimated nutrition needs source URL or detailed preparation/measurement notes')


def create_examples(image_b64: str, items: list[dict], photo_group: str, plate_diameter_cm: float | None = None, rights_confirmed: bool = False) -> dict:
    if rights_confirmed is not True:
        raise ValueError('Admin must confirm rights to store and train on this food photograph')
    validate_items(items)
    if plate_diameter_cm is not None and (not math.isfinite(plate_diameter_cm) or not 10 <= plate_diameter_cm <= 40):
        raise ValueError('Plate diameter must be 10-40cm or omitted')
    if not 3 <= len(photo_group.strip()) <= 100:
        raise ValueError('A 3-100 character session/batch group prevents train/test leakage')
    raw = normalize_image(image_b64)
    photo_id, path = persist_photo(raw)
    ids = [str(uuid.uuid4()) for _ in items]
    try:
        with connection() as c:
            c.execute('''INSERT INTO learning_photos
              (id,image_sha,dhash,image_path,photo_group,dataset_split,created_at,plate_diameter_cm,rights_attested)
              VALUES (?,?,?,?,?,?,?,?,?)''', (photo_id,hashlib.sha256(raw).hexdigest(),dhash(raw),path,photo_group.strip(),group_split(photo_group.strip()),now(),plate_diameter_cm,1))
            for sample_id, item in zip(ids, items):
                basis=item.get('nutrient_basis','per_100g')
                normalizer=100/item['grams'] if basis=='total_for_weighed_portion' else 1
                c.execute('''INSERT INTO learning_examples
                  (id,photo_id,name,recipe_variant,grams,unit,kcal,protein,carbs,fat,source_kind,evidence_url,note,bbox_json,status,approved_at,created_at,input_basis,weight_basis)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                  sample_id,photo_id,item['name'].strip(),str(item.get('recipe_variant') or '').strip(),
                  item['grams'],'g',*(round(item[k]*normalizer,4) for k in NUMERIC),item['source_kind'],
                  str(item.get('evidence_url') or '').strip(),str(item.get('note') or '').strip(),
                  json.dumps(item.get('bbox')) if item.get('bbox') else None,'pending',None,now(),basis,item.get('weight_basis','estimated')))
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise
    return {'photo_id':photo_id,'example_ids':ids,'status':'pending_review','split':group_split(photo_group.strip()),
            'note':'Each food must be approved separately before a user can see a reference.'}


def list_examples(status: str = 'pending'):
    if status not in ('pending','approved','rejected','revoked','all'):
        raise ValueError('Invalid status')
    with connection() as c:
        sql='''SELECT e.*,p.photo_group,p.dataset_split,p.image_sha,p.plate_diameter_cm,p.rights_attested FROM learning_examples e
               JOIN learning_photos p ON p.id=e.photo_id'''
        if status != 'all':
            rows=c.execute(sql+' WHERE e.status=? ORDER BY e.created_at DESC LIMIT 200',(status,)).fetchall()
        else:
            rows=c.execute(sql+' ORDER BY e.created_at DESC LIMIT 200').fetchall()
    return [{**dict(row),'bbox':json.loads(row['bbox_json']) if row['bbox_json'] else None} for row in rows]


def review_sample(sample_id: str, decision: str):
    if decision not in ('approved','rejected'):
        raise ValueError('Invalid decision')
    with connection() as c:
        row=c.execute('SELECT status FROM learning_examples WHERE id=?',(sample_id,)).fetchone()
        if not row:
            raise LookupError('No such example')
        if row['status']!='pending':
            raise ValueError('This example has already been reviewed; a revised sample requires a new record')
        c.execute('UPDATE learning_examples SET status=?,approved_at=? WHERE id=?',
                  (decision,now() if decision=='approved' else None,sample_id))
    return {'example_id':sample_id,'status':decision}


def revoke_sample(sample_id: str, reason: str):
    """Immediate fail-closed retraction of a bad admin reference, without erasing its audit trail.

    Existing user diary entries remain historical; references and training exports
    exclude revoked examples. Any replacement must be uploaded and reviewed anew.
    """
    reason = reason.strip()
    if not 8 <= len(reason) <= 400:
        raise ValueError('Revocation requires an 8-400 character reason')
    with connection() as c:
        r = c.execute('SELECT status FROM learning_examples WHERE id=?',(sample_id,)).fetchone()
        if r is None:
            raise LookupError('No such example')
        if r['status'] != 'approved':
            raise ValueError('Only approved examples can be revoked')
        c.execute('UPDATE learning_examples SET status=?,note=note||? WHERE id=?',
                  ('revoked','\nREVOKED '+now()+': '+reason,sample_id))
    return {'example_id':sample_id,'status':'revoked',
            'note':'Reference withdrawn from live matching and future training exports; previous meal history retained.'}


def food_object(row: dict) -> dict:
    return {'id':'learned:'+row['id'],'name':row['name'],'category':'Admin-reviewed reference',
            'default_grams':row['grams'],'kcal':row['kcal'],'protein':row['protein'],
            'carbs':row['carbs'],'fat':row['fat'],
            'source':f"admin_reviewed:{row['source_kind']}",
            'evidence_url':row['evidence_url'], 'aliases':[],
            'note':'Reference nutrition per 100g. Different oil/recipe variations change values.'}


def get_approved_food(food_id: str) -> dict | None:
    if not food_id.startswith('learned:'):
        return None
    with connection() as c:
        row=c.execute('''SELECT e.* FROM learning_examples e JOIN learning_photos p ON p.id=e.photo_id
                  WHERE e.id=? AND e.status=? AND p.rights_attested=1''',(food_id[8:],'approved')).fetchone()
    return food_object(dict(row)) if row else None


def compare_photo(image_bytes: bytes, max_distance: int = 5):
    """Exact photo can restore recorded serving; near photos provide label suggestions only."""
    fingerprint = hashlib.sha256(image_bytes).hexdigest()
    observed_hash = int(dhash(image_bytes), 16)
    with connection() as c:
        rows=c.execute('''SELECT e.*,p.image_sha,p.dhash,p.photo_group,p.dataset_split FROM learning_examples e
            JOIN learning_photos p ON p.id=e.photo_id WHERE e.status='approved' AND p.rights_attested=1 ORDER BY e.approved_at DESC LIMIT 1500''').fetchall()
    exact=[];near=[]
    for r in rows:
        item=dict(r)
        dist = (int(item['dhash'],16) ^ observed_hash).bit_count()
        if item['image_sha'] == fingerprint:
            exact.append(item)
        elif dist <= max_distance:
            near.append((dist,item))
    if exact:
        return {'match_type':'exact_photo','items':[
            {'detected_name':r['name'],'food':food_object(r),'grams':r['grams'],'min_grams':None,'max_grams':None,
             'portion_method':'admin_recorded_for_identical_photo','mass_is_measured':False,
             'requires_match':False,'needs_confirmation':True,'reference_id':r['id'],
             'warning':'Admin recorded this serving in an identical reference photo. Recheck if it is not your portion.'}
            for r in exact], 'candidates':[]}
    # Never call dHash distance a probability or calibrated model confidence.
    near.sort(key=lambda x:(x[0],x[1]['name']))
    candidates=[];seen=set()
    for distance,r in near:
        identity=(r['name'].casefold(),r['recipe_variant'].casefold())
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append({'food':food_object(r),'reference_id':r['id'],
                           'perceptual_distance':distance,'grams':None,
                           'warning':'Visually similar, NOT verified same food or same amount; choose manually.'})
        if len(candidates)>=5:break
    if not candidates:
        # Optional semantic retrieval helps with different angles/plates, but
        # still never carries the admin reference's gram amount into a new scan.
        from .semantic_retrieval import candidates as semantic_candidates
        try:candidates=semantic_candidates(image_bytes)
        except (RuntimeError,ImportError,OSError):candidates=[]
    return {'match_type':'similar_photo_candidates' if candidates else 'no_match',
            'items':[], 'candidates':candidates}


def create_feedback(profile: str, corrected_name: str, corrected_grams: float | None,
                    comment: str, reference_id: str | None, consent: bool, image_b64: str | None,
                    training_consent: bool = False):
    if not consent:
        raise ValueError('Explicit consent is required to submit information to the admin review queue')
    if not 2 <= len(corrected_name.strip()) <= 120 or len(comment) > 500:
        raise ValueError('Invalid correction label/comment')
    if corrected_grams is not None and (not math.isfinite(corrected_grams) or not 1 <= corrected_grams <= 5000):
        raise ValueError('Invalid corrected serving')
    if training_consent and not image_b64:
        raise ValueError('Training consent requires a shared reference photo')
    path=None
    if image_b64:
        raw=normalize_image(image_b64)
        _, path=persist_photo(raw)
    feedback_id=str(uuid.uuid4())
    try:
        with connection() as c:
            c.execute('''INSERT INTO learning_feedback
              (id,profile,reference_id,corrected_name,corrected_grams,comment,image_path,consent,status,created_at,training_consent)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (feedback_id,profile,reference_id,corrected_name.strip(),corrected_grams,comment,path,1,'pending',now(),int(training_consent)))
    except BaseException:
        if path:Path(path).unlink(missing_ok=True)
        raise
    return {'feedback_id':feedback_id,'status':'pending_review',
            'note':'Feedback does not train or overwrite an approved nutrition record automatically'}


def list_feedback(status='pending'):
    if status not in ('pending','approved','rejected','all'):
        raise ValueError('Invalid status')
    with connection() as c:
        rows=c.execute('SELECT * FROM learning_feedback '+('' if status=='all' else 'WHERE status=? ')+
                       'ORDER BY created_at DESC LIMIT 200',() if status=='all' else (status,)).fetchall()
    # Avoid exposing profile identifiers in the admin UI; do not disclose submitted image paths.
    return [{k:r[k] for k in ('id','reference_id','corrected_name','corrected_grams','comment','status','created_at')} |
            {'has_image':bool(r['image_path']),'training_consent':bool(r['training_consent'])}
            for r in rows]


def feedback_photo_path(feedback_id: str) -> Path:
    """Admin-authorized read-only preview; no disk path is revealed to clients."""
    with connection() as c:
        r=c.execute('SELECT image_path FROM learning_feedback WHERE id=?',(feedback_id,)).fetchone()
    if not r or not r['image_path']:
        raise LookupError('No photo available for this correction')
    p=Path(r['image_path'])
    if not p.is_file() or p.suffix != '.jpg':
        raise LookupError('The private correction photo is unavailable')
    return p


def review_feedback(feedback_id:str,decision:str):
    if decision not in ('approved','rejected'):raise ValueError('Invalid decision')
    with connection() as c:
        current=c.execute('SELECT status FROM learning_feedback WHERE id=?',(feedback_id,)).fetchone()
        if not current:raise LookupError('Feedback missing')
        if current['status'] != 'pending':raise ValueError('Feedback already reviewed')
        c.execute('UPDATE learning_feedback SET status=? WHERE id=?',(decision,feedback_id))
    return {'feedback_id':feedback_id,'status':decision,
            'note':'Review alone does not create a training example; label, weight and nutrition require admin verification.'}


def statistics():
    with connection() as c:
        indexed_images=c.execute('SELECT COUNT(DISTINCT photo_id) FROM learning_embeddings').fetchone()[0]
        sample_status=dict(c.execute('SELECT status,COUNT(*) AS n FROM learning_examples GROUP BY status').fetchall())
        feedback_status=dict(c.execute('SELECT status,COUNT(*) AS n FROM learning_feedback GROUP BY status').fetchall())
        splits=dict(c.execute('''SELECT p.dataset_split,COUNT(*) AS n FROM learning_examples e
                          JOIN learning_photos p ON p.id=e.photo_id
                          WHERE e.status='approved' GROUP BY p.dataset_split''').fetchall())
    return {'samples':sample_status,'feedback':feedback_status,'approved_split_counts':splits,
            'semantic_indexed_photos':indexed_images,
            'real_photo_recognition_accuracy':None,'food_detection_map50':None,
            'portion_weight_mae_g':None,'protein_mae_g':None,
            'training_status':'curated_examples_available_not_trained',
            'message':'An expanding database does not prove accuracy or automatically update model weights.'}


def export_manifest():
    with connection() as c:
        rows=c.execute('''SELECT e.*,p.photo_group,p.dataset_split,p.image_path,p.image_sha,p.plate_diameter_cm,p.rights_attested
             FROM learning_examples e JOIN learning_photos p ON p.id=e.photo_id
             WHERE e.status='approved' AND p.rights_attested=1 ORDER BY p.dataset_split,e.id''').fetchall()
    return [{'id':r['id'],'photo_id':r['photo_id'],'image_path':r['image_path'],
             'name':r['name'],'recipe_variant':r['recipe_variant'], 'grams':r['grams'],
             'bbox':json.loads(r['bbox_json']) if r['bbox_json'] else None,
             'nutrition_per_100g':{k:r[k] for k in NUMERIC},'source_kind':r['source_kind'],
             'evidence_url':r['evidence_url'],'dataset_split':r['dataset_split'],
             'photo_group':r['photo_group'],'plate_diameter_cm':r['plate_diameter_cm'],
             'weight_basis':r['weight_basis'],'rights_attested':bool(r['rights_attested'])} for r in rows]


def validation_gates():
    """Admin-facing readiness; never claim accuracy without real held-out evidence."""
    with connection() as c:
        approved=c.execute("SELECT COUNT(*) FROM learning_examples WHERE status='approved'").fetchone()[0]
        weighed=c.execute("SELECT COUNT(*) FROM learning_examples WHERE status='approved' AND weight_basis='scale'").fetchone()[0]
        boxes=c.execute("SELECT COUNT(*) FROM learning_examples WHERE status='approved' AND bbox_json IS NOT NULL").fetchone()[0]
        splits=dict(c.execute('''SELECT p.dataset_split,COUNT(*) FROM learning_examples e
            JOIN learning_photos p ON p.id=e.photo_id WHERE e.status='approved' AND p.rights_attested=1
            GROUP BY p.dataset_split''').fetchall())
    def entry(i,name,status='unmeasured',count=None):
        d={'id':i,'name':name,'status':status,'metric':None}
        if count is not None:d['count']=count
        return d
    gates=[
      entry('reviewed_examples','Approved, rights-cleared food annotations','collecting',approved),
      entry('actual_scale_weight','Scale-weighed edible portion examples','collecting',weighed),
      entry('mixed_plate_boxes','Reviewed item bounding boxes','collecting',boxes),
      entry('train_examples','Training split annotations','collecting',splits.get('train',0)),
      entry('validation_examples','Validation split annotations','collecting',splits.get('validation',0)),
      entry('blind_test_examples','Held-out test split annotations','collecting',splits.get('test',0)),
      entry('trained_food_model','Trained and evaluated Reliv food classifier','not_validated'),
      entry('trained_detector','Trained and evaluated multi-food detector','not_validated'),
      entry('mAP50','Real-image food detector mAP@0.50'),
      entry('mAP50_95','Real-image food detector mAP@0.50:0.95'),
      entry('recognition_accuracy','Independent food label top-1 accuracy'),
      entry('grams_mae','Scale-weighed food mass MAE in grams'),
      entry('100_vs_300','100g versus 300g balanced holdout distinction'),
      entry('calorie_mae','Ground-truth edible meal kcal MAE'),
      entry('protein_mae','Verified recipe protein MAE in grams'),
      entry('unknown_food_rejection','Unknown/unseen food rejection rate'),
      entry('regional_coverage','Representative Indian/South Indian/street food coverage'),
      entry('branded_exact_variant','Packaged SKU matching checked against package labels','not_validated'),
      entry('privacy_deletion','User data deletion and retention controls','not_implemented'),
      entry('mobile_e2e','Real Android/iOS end-to-end QA','not_validated'),
      entry('rbac_mfa','Production administrator SSO/RBAC/MFA','not_implemented'),
      entry('independent_comparison','Blinded market competitor comparison'),
    ]
    return {'production_ready':False,'gates':gates,
            'warning':'Data collection does not itself constitute passing accuracy validation.'}
