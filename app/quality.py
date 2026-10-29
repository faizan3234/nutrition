"""Explain the provenance of nutrients and whether any gram estimate is measured.

A nutrition source is not a model validation score; do not conflate them.
"""

def nutrition_quality(source:str, weight_basis:str='manual') -> dict:
    source=(source or '').casefold()
    if 'illustrative' in source or source.startswith('generic_'):
        tier='illustrative'; label='Starter estimate'; warning='Example nutrient values; not verified for this recipe.'
    elif 'off:' in source or 'open food facts' in source:
        tier='community_label';label='Community product label';warning='Check the exact package label and preparation.'
    elif 'usda' in source or 'fooddata central' in source or 'ifct' in source or 'indb' in source:
        tier='reference_database';label='Food composition reference';warning='Confirm the exact ingredient, cooking method and source record.'
    elif 'weighed_recipe' in source:
        tier='recipe_calculated';label='Weighed recipe';warning='Depends on ingredient data and actual cooked yield.'
    elif 'packaged_label' in source or 'user_label' in source:
        tier='user_label';label='Package label entered by user';warning='Review the label; values have not been independently verified.'
    else:
        tier='estimated';label='Nutrition estimate';warning='Recipe and serving could differ.'
    return {'tier':tier,'label':label,'warning':warning,
            'weight_basis':weight_basis,
            'measured_weight':weight_basis=='scale',
            'accuracy_validated':False}
