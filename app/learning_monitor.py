"""Read-only admin triage: highlight frequent errors and contradictory approved records."""
from collections import Counter,defaultdict
from .db import connection

def triage():
    with connection() as db:
        feedback=db.execute('''SELECT corrected_name, reference_id, status FROM learning_feedback''').fetchall()
        approved=db.execute('''SELECT id,name,recipe_variant,kcal,protein,carbs,fat FROM learning_examples WHERE status='approved' ''').fetchall()
    counts=Counter(x['corrected_name'].strip().casefold() for x in feedback)
    byname=defaultdict(list)
    for row in approved:byname[(row['name'].casefold(),row['recipe_variant'].casefold())].append(dict(row))
    conflicts=[]
    for (name,variant),rows in byname.items():
        if len(rows)<2:continue
        for k in ('kcal','protein','carbs','fat'):
            vals=[float(x[k]) for x in rows]
            if max(vals)-min(vals)>max(5,0.25*max(vals)):
                conflicts.append({'food':name,'variant':variant,'metric':k,'values':vals,
                                  'example_ids':[r['id'] for r in rows],
                                  'warning':'Review evidence; different recipes can legitimately have different nutrients.'})
    return {'frequent_corrections':[{'food':name,'count':count} for name,count in counts.most_common(30)],
            'possible_nutrition_conflicts':conflicts,'approved_example_count':len(approved),
            'note':'Triage only; no automatic change to weights, labels or model.'}
