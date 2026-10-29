"""Profile-scoped plate calibration and reusable food shortcuts.

These are convenience tools, not a trained portion estimator. Production access
is enforced by the existing Reliv JWT bridge at API boundaries.
"""
from __future__ import annotations
from datetime import datetime, timezone
import uuid
from .db import connection
from .catalog import LOOKUP, nutrients, serving_unit


def initialize():
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS plate_profiles (
            profile TEXT PRIMARY KEY, diameter_cm REAL NOT NULL,
            label TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS food_shortcuts (
            id TEXT PRIMARY KEY, profile TEXT NOT NULL, food_id TEXT NOT NULL,
            nickname TEXT NOT NULL, serving_amount REAL NOT NULL,
            created_at TEXT NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS food_shortcuts_profile ON food_shortcuts(profile)')


def save_plate(profile, diameter_cm, label):
    ts=datetime.now(timezone.utc).isoformat()
    with connection() as db:
        db.execute('''INSERT INTO plate_profiles(profile,diameter_cm,label,updated_at)
           VALUES (?,?,?,?) ON CONFLICT(profile) DO UPDATE SET
           diameter_cm=excluded.diameter_cm,label=excluded.label,updated_at=excluded.updated_at''',
                   (profile, diameter_cm, label, ts))
    return {'profile': profile,'diameter_cm':diameter_cm,'label':label,'updated_at':ts,
            'warning':'Reference diameter is user-entered; it does not measure grams.'}


def get_plate(profile):
    with connection() as db:
        x=db.execute('SELECT * FROM plate_profiles WHERE profile=?',(profile,)).fetchone()
    return dict(x) if x else None


def add_shortcut(profile, food_id, serving_amount, nickname):
    if food_id not in LOOKUP:raise LookupError('Food is not in the generic catalogue')
    x={'id':str(uuid.uuid4()),'profile':profile,'food_id':food_id,
       'nickname':nickname,'serving_amount':serving_amount,
       'created_at':datetime.now(timezone.utc).isoformat()}
    with connection() as db:
        db.execute('''INSERT INTO food_shortcuts (id,profile,food_id,nickname,serving_amount,created_at)
                      VALUES (:id,:profile,:food_id,:nickname,:serving_amount,:created_at)''',x)
    return x


def list_shortcuts(profile):
    with connection() as db:
        rows=db.execute('SELECT * FROM food_shortcuts WHERE profile=? ORDER BY created_at DESC',(profile,)).fetchall()
    return [{**dict(r),'food_name':LOOKUP.get(r['food_id'],{}).get('name','Unknown'),
             'unit':serving_unit(LOOKUP[r['food_id']]) if r['food_id'] in LOOKUP else 'g'} for r in rows]


def shortcut_meal(profile, shortcut_id, fraction, meal):
    with connection() as db:
        row=db.execute('SELECT * FROM food_shortcuts WHERE id=? AND profile=?',(shortcut_id,profile)).fetchone()
    if not row:raise LookupError('Shortcut not found')
    food=LOOKUP.get(row['food_id'])
    if not food:raise LookupError('Food no longer in catalogue; review shortcut')
    grams=round(row['serving_amount'] * fraction,2)
    if not 0 < grams <=5000:raise ValueError('Invalid amount')
    return {'food_id':food['id'],'food_name':food['name'],'grams':grams,
            'unit':serving_unit(food),'meal':meal,'source':food['source'],**nutrients(food,grams)}
