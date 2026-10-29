"""Independent, held-out benchmark report; never uses training metrics as live accuracy."""
import math
from collections import defaultdict

def summarize(rows:list[dict]) -> dict:
    if not rows:raise ValueError('Need at least one independent labeled test meal')
    if len(rows)>100000:raise ValueError('Too many rows')
    ids=set();items=[]
    for row in rows:
        sid=row.get('sample_id')
        if not sid or sid in ids:raise ValueError('Distinct sample_id required')
        ids.add(sid)
        if row.get('split')!='test':raise ValueError('Only held-out test records may be evaluated')
        metrics={}
        for field in ('grams','kcal','protein'):
            truth=row.get('true_'+field);pred=row.get('predicted_'+field)
            if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in (truth,pred)):
                raise ValueError('Missing or invalid '+field+' measurements')
            metrics[field]=abs(truth-pred)
        items.append({'matched':str(row.get('true_label','')).strip().casefold()==str(row.get('predicted_label','')).strip().casefold(),
                      'group':row.get('group','unspecified'),**metrics})
    n=len(items)
    metrics={'top1_recognition_accuracy_percent':round(100*sum(x['matched'] for x in items)/n,2)}
    for key in ('grams','kcal','protein'):
        metrics[key+'_mae']=round(sum(x[key] for x in items)/n,2)
    groups=defaultdict(list)
    for x in items:groups[x['group']].append(x)
    return {'sample_count':n,'split':'test','metrics':metrics,
            'by_group':{group:{'count':len(vals),'recognition_accuracy_percent':round(100*sum(v['matched'] for v in vals)/len(vals),2),
                               'grams_mae':round(sum(v['grams'] for v in vals)/len(vals),2)}
                        for group,vals in groups.items()},
            'not_measured':['detection_mAP50','detection_mAP50_95'],
            'warning':'Metrics only describe supplied held-out labeled samples, not the market or all cuisines.'}
