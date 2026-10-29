import pytest
from scripts.evaluate import evaluate
from scripts.audit_calculations import check


def test_benchmark_uses_ground_truth_and_measures_errors():
    r=evaluate([
       {'meal_id':'dish1','true_grams':'100','predicted_grams':'120','true_kcal':'200','predicted_kcal':'220','true_protein':'10','predicted_protein':'11'},
       {'meal_id':'dish2','true_grams':'300','predicted_grams':'270','true_kcal':'600','predicted_kcal':'540','true_protein':'30','predicted_protein':'27'},
    ])
    assert r['components']==2
    assert r['metrics']['grams']['mean_absolute_error']==25
    assert r['metrics']['grams']['mean_absolute_percentage_error_nonzero_truth']==15
    assert r['metrics']['kcal']['mean_absolute_error']==40
    assert r['metrics']['protein']['mean_absolute_error']==2


def test_benchmark_doesnt_fake_results_without_predictions():
    with pytest.raises(ValueError):evaluate([])


def test_full_catalog_arithmetic_sweep():
    r=check()
    assert r['foods']>=170
    assert r['failed']==0
    assert r['nutrient_arithmetic_checks']==r['foods']*10*4


def test_real_vision_benchmark_requires_configured_provider():
    from scripts.evaluate_photos import benchmark
    import os
    assert os.getenv('VISION_PROVIDER','none')=='none'
    with pytest.raises(RuntimeError,match='No vision model configured'):
        benchmark([{'image_path':'irrelevant.jpg','true_food_name':'Idli'}],__import__('pathlib').Path('/tmp'))
