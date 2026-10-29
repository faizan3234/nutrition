# Reliv camera accuracy & portion benchmark — 29 October 2026

| Metric | Reliv v0.5 measured value | Why |
|---|---|---|
| Camera top-1 recognition accuracy | **Not measured (N/A)** | No executed held-out model inference with labeled real food photos |
| Mixed-food bounding-box mAP50 | **Not measured (N/A)** | No annotated real-image prediction set |
| Mixed-food mAP50:95 | **Not measured (N/A)** | Same blocker |
| Edible gram MAE | **Not measured (N/A)** | No known-mass photo pairs processed |
| Classification of 100g vs 300g from photo | **Not measured (N/A)** | No scale-validated classifier trained/tested |
| Calories MAE, protein MAE from photo | **Not measured (N/A)** | Nutrition & grams are not independently validated |
| Code calculations | **7,720/7,720 passed** | Deterministic per-100 math on illustrative values, **NOT nutrition accuracy** |
| Unit/API tests | See current pytest output | Synthetic/mock test data, **NOT camera benchmark** |

External developer-reported NutriLens 90.94% 22-class recognition and BhojanAI 0.806 detection mAP50 must **not** be claimed as Reliv measurements. 193 searchable categories also does **not** mean 193 trained recognition labels. All model weights are operator-provided; this release has none bundled.

## Legitimate public benchmarks

**Nutrition5k**: Google, 5,006 plates, ingredients, weights and calories, official test split, commercial-friendly CC BY 4.0, but mostly California cafeteria food and ~181GB full download. https://github.com/google-research-datasets/Nutrition5k

**Indian food images**: Dataset rights and dish labels must be checked before use. A food-classification label alone does not establish per-item grams or multi-food bounding-box labels. Adding these labels requires additional human annotation and kitchen-scale measurement.

## Exact reproduction (once data and model weights are present)

- `python -m scripts.evaluate_photos heldout_images.csv --out image_metrics.json` for exact food classification and mass estimates; the CSV must identify *real* photos, food labels, and weighed values.
- `python -m scripts.evaluate_detection --ground-truth heldout_boxes.json --predictions model_outputs.json --out detection_metrics.json` to calculate class-aware mAP50 and mAP50:95.
- `python -m scripts.evaluate weighed_meals.csv --json` for grams/kcal/protein MAE and MAPE from actual reference and model predictions.
- `python -m scripts.audit_release_gates` for a machine-readable release gate (currently **FAIL**).

**Benchmark protocol:** freeze model, train/val/test group split; avoid near-duplicate photos and plate photos from the same cooking session crossing splits; at least 100g/300g matched portions with kitchen scale; evaluate performance by dish, restaurant, lighting, phone, region, vessel, measured vs guessed quantities, and high/low confidence. Cite uncertainty intervals, discard rates and all failures; do not cherry-pick demo photos.

## Why this benchmark could not be completed here

- Runtime has no Internet DNS access to download weights or image datasets. The GitHub connector can inspect code but does not provide a binary container data path for the large models; the model downloads failed.
- No private provider API key or external hardware camera was available to run cloud vision or camera regression.
- No accurately weighed Indian serving labels or held-out bounding boxes were supplied to this runtime.

**No real-food mAP or recognition number is being invented.**
