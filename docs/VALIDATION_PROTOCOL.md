# Reliv Nutrition AI — independent validation protocol

## Zero ambiguity: four different things need four different measurements

1. **Single-food top-1 accuracy:** correct labels / held-out food images (plus top-5 and a classwise confusion matrix). Classification is not detection.
2. **Mixed-plate detection mAP:** AP at IoU 0.50 and mAP over IoU 0.50–0.95; include classes, image counts and all detection thresholds. Evaluate against annotated per-food boxes/segments.
3. **Weight and volume:** mean absolute error (MAE) in grams, median absolute error, mean absolute percentage error (MAPE) for nonzero truth, P90 errors, and percentage correctly distinguishing ~100g from ~300g.
4. **Nutrients:** per-meal and per-item MAE/MAPE for energy kcal, protein g, carbs g, fat g; compare against the weighed meal's actual ingredients and recipe preparation, not just an assumed generic dish table.

**Current results for all four image-driven measurements: NOT MEASURED.** Software arithmetic tests are separate.

## Dataset options and rights

- [Google Nutrition5k](https://github.com/google-research-datasets/Nutrition5k): 5,006 plates, measured total mass/calories/macros, official train/test split, CC BY 4.0 data. The complete dataset is ~181.4 GB. **Californian cafeteria sampling bias**; inadequate alone to assess India.
- [SohlHealth enhanced Indian food classification](https://huggingface.co/datasets/SohlHealth/enhanced-indian-food-classification): 15,404 images across 43 classes (dataset card; CC BY 4.0), train/validation/test partitions. Classification images do **not** provide reliable gram or ingredient weights.
- [Google FoodLens paper](https://research.google/pubs/foodlens-fine-grained-and-multi-label-classification-ofindian-food-images/): research into 140+ Indian dishes with ~30K multilabel examples. Confirm whether its dataset and weights are actually released before planning to use it.
- [Khana Indian food dataset](https://khana.omkarprabhu.in/): research/education restrictions. **Do not train a commercial Reliv product on it without permission**.
- For exact branded products, community product data via [Open Food Facts](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/) require ODbL compliance and verification against the sold label.

## What qualifies as a valid real-world camera benchmark

1. Identify license-compatible food datasets, download legally, pin exact release and record hashes.
2. Create a dataset manifest with photo IDs, recipe/food category, physical meal group IDs, venue, camera and packaging provenance.
3. Keep all photos of each meal in the same split: use `python -m training.split_by_group manifest.csv --out dataset/split_manifests`.
4. Never use the author's validation set as the sole independent test. Collect a separate hidden holdout across new venues and phones.
5. For mixed thalis, annotate each visible dish with a bounding box or polygon and independently weigh each item immediately before photography. Use accurate scales (tare calibrated).
6. Image capture conditions: two device tiers, different cuisines, rice and dal, sauces, sausage, pizza, pasta, dosa, fast food, clear and opaque drinks, side-angle plus top view, different plate diameters, low/high lighting.
7. Label grams, millilitres, recipes, cooked/raw status, brand SKU, ingredient grams, oil/ghee amounts and nutrition source.
8. Freeze trained weights and thresholds before opening holdout data.
9. Generate inference JSON or CSV **by actually running the deployed model**. No assumed scores, fabricated rows, or reference values filled from predictions.
10. Run `python -m scripts.evaluate_detection --ground-truth gt.json --predictions pred.json --out detection_metrics.json` on mixed plates.
11. Run `python -m scripts.evaluate_photos holdout.csv --out image_results.json` for classification and mass estimates (where provider supports them).
12. Run `python -m scripts.evaluate weighed_components.csv --json` for gram/kcal/protein MAE.
13. Publish class-wise sample counts and 95% bootstrap confidence intervals. Disclose skipped/failed scans; they count as failures, not quietly dropped.
14. Report both broad-coverage performance **and** narrower 22-class benchmark performance separately.
15. Compare on the *same* blinded dataset with multiple existing nutrition apps under identical camera and correction settings before claiming market leadership.
16. Independent reviewers inspect code, weigh ingredients, and replicate reported metrics.

## Minimum prelaunch acceptance gates (proposed, not achieved)

These are proposed quality gates, *not a claim the targets are met*. Refine after observing real-world error distributions.

- At least 500 independent held-out photographed meals across Indian and international foods, with a representative mixed-plate subset; more images required for credible per-class estimates.
- Per-class detection and classification metrics including unknown-food rejection.
- Portion 100g versus 300g distinction tested with balanced ground truth. Publish sensitivity/specificity and confidence intervals, not just a single percentage.
- Portion mass and nutrient errors reported with stratification by liquid, curry, rice, bread, snack, pizza, pasta, packaged product and mixed plate.
- Nutrition source provenance for every displayed item, with missing data blocked or flagged.
- Successful iOS and Android smoke tests, accessibility, rate limits, authentication and data-deletion review.

## Why we cannot infer high accuracy from source projects

Upstream 90.94% NutriLens = reported classification of 22 predefined categories; BhojanAI 0.806 mAP50 = detection on 20 classes. Neither measures grams or nutrient error for **this** new Reliv release. Scores are not mathematically mergeable. Adding 193 searchable labels does not train an image model on 193 visual categories.

A published peer-reviewed study using 52 standardised food photos found substantial food-weight and energy error in general-purpose multimodal LLMs: [Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from Food Images](https://pubmed.ncbi.nlm.nih.gov/41081011/). Accurate nutritional assessment from photographs remains technically hard, especially with mixed curries and hidden ingredients.
