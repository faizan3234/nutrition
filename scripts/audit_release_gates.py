"""Fail-closed release-gate report: no sample photo or metric is invented."""
import json,os
from pathlib import Path
from datetime import date
from app.catalog import FOODS
from app.vision import model_info

def main():
    root=Path(__file__).resolve().parent.parent
    sources={s:sum(f['source']==s for f in FOODS) for s in {f['source'] for f in FOODS}}
    info=model_info()
    # These files are operator-provided after actual benchmark, never auto-generated.
    evidence=root/'evidence'
    required={
      'independent_classification':evidence/'recognition_heldout.json',
      'independent_detection':evidence/'detection_heldout.json',
      'measured_portion_regression':evidence/'portion_heldout.json',
      'source_verified_nutrition':evidence/'food_source_audit.json',
      'deployed_mobile_qa':evidence/'device_qa.json',
      'deployment_security_review':evidence/'security_qa.json',
      'comparative_competitor_study':evidence/'competitor_comparison.json'
    }
    # Merely placing evidence files does not establish passing: requires explicit
    # benchmark evaluator verification; we don't automatically approve them here.
    metrics={'top1_accuracy':None,'mAP50':None,'mAP50_95':None,'portion_mass_mae_g':None,
             'portion_100g_vs_300g_confusion_matrix':None,'calorie_mae_kcal':None,'protein_mae_g':None}
    result={'release':'Reliv Nutrition AI v0.6.0-source-handoff','audit_date':str(date.today()),
      'catalog_searchable_foods':len(FOODS),'nutrition_sources':sources,
      'camera_provider':info['provider'],'provider_ready':info['ready'],
      'real_model_benchmark_images_executed_in_this_release':0,
      'real_model_benchmark_predictions_executed_in_this_release':0,
      'camera_metrics':metrics,'evidence_expected':{k:str(v.relative_to(root)) for k,v in required.items()},
      'evidence_present':{k:v.is_file() for k,v in required.items()},
      'production_gate_passed':False,
      'primary_blockers':['No trained approved weights/API inference verified against held-out labeled photos',
          'No independent Indian-meal weighed-portion results',
          'Illustrative catalogue not replaced by vetted food composition source',
          'Production auth integration and security review remain untested on deployment',
          'Real Android/iPhone verification and competitor comparative trials incomplete'],
      'claim_allowed':'Software prototype with validated arithmetic and tested API code',
      'claim_prohibited':'Highest accuracy, exact food weighing, market leading, all foods recognized, medically validated'}
    path=root/'docs'/'RELEASE_GATE_AUDIT_CURRENT.json'
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return result
if __name__=='__main__':main()
