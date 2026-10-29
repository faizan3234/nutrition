# Reliv Nutrition AI — Original v0.1 Accuracy Audit

> Superseded for current software-test counts by [v0.2 camera readiness report](CAMERA_ACCURACY_AND_RELEASE.md). This baseline remains to preserve the original test record.
**Audit date:** 29 October 2026  
**Scope:** Current project v0.1, untrained/default configuration; source-repository claims evaluated separately.

## Executive result

**Photo recognition accuracy: NOT MEASURED.** The installed default provider is `VISION_PROVIDER=none`.
**Photo portion-weight accuracy: NOT MEASURED.** The project does not currently estimate weight from photos without an optional external AI provider, which is not calibrated or verified.
**Calorie/protein accuracy against weighed meals: NOT MEASURED.** Starter nutrient values are illustrative, not a validated composition database.

**Nutrient scaling software arithmetic: 6,840/6,840 checks passed** over 171 dishes, 10 manually specified weights (5–900 g), 4 nutrient outputs (kcal, protein, carbohydrate, fat). This tests *only* the computation of `(per-100g value × manually supplied grams / 100)`; it is **not** nutrition or vision model accuracy. A previous implementation had 146 cases of rounding disagreements under an independently specified decimal rounding policy. It was corrected to explicit decimal `ROUND_HALF_UP`; checks now pass.

**Automated suite:** 10 Python tests passed, including health API, food search, logged meals, image validation, missing model behavior, benchmark math, and 100 g / 300 g nutrient scaling.

## Why we have no defensible camera model accuracy yet

The newly assembled codebase is modular but does not contain trained model weights. Optional external models available from GitHub were located but could not be installed and run locally in this environment: external binary weight/data downloads were unavailable. Consequently **no actual predictions on the public datasets were generated**. We did not infer recognition accuracy from food-count coverage or claim that passing unit tests validates photo recognition.

## External datasets identified, not executed against a model

1. [Google Nutrition5k](https://github.com/google-research-datasets/Nutrition5k): 5,006 dishes with measured mass, protein, calories, carbs/fat and RGB/RGB-D images, with official splits; the full raw archive is approximately 181.4GB. Western-cafeteria biased and not a dedicated Indian food benchmark. License CC BY 4.0. Best for real weight/nutrient regression once an image-to-gram predictor exists.
2. [Indian food image classification](https://images.cv/dataset/indian-food-image-classification-dataset): 2,824 labeled photos in 21 Indian categories, downloadable through the provider (API key/access may be required). Suitable for independent food class evaluation with category harmonization; no verified gram labels.
3. [Kaggle Food Recognition Challenge 2022](https://www.kaggle.com/competitions/food-recognition-challenge-2022/data): 30,612 training and 7,653 test photos, 80 classes; competition rules and access restrictions apply. No per-serving weight ground truth.
4. [RASOI](https://fkg-india.github.io/library/datasets/): Indian thali segmentation and food bounding boxes, noncommercial research license CC BY-NC-SA 4.0; verify rights before commercial training.

## External upstream metrics — NOT this project's measurements

- [NutriLens (programcode20)](https://github.com/programcode20/NutriLens) reports 90.94% top-1 classification over its 22 Indian dish categories; **not** portion or mixed-thali accuracy.
- [BhojanAI](https://github.com/shreyasvankhede/BhojanAI-IndianFoodCalorieTracker) reports 0.806 detection mAP@0.5 for its 20 categories; **not** the same metric as 90.94% top-1.
- [Offline Nutrilens (thejusdutt)](https://github.com/thejusdutt/nutrilens) reports 81.1% top-1 on 259 extended Indian images with a 231-item vocabulary; this is author-reported, not re-run here.

## Reproduction steps

```bash
pip install -r requirements.txt
python -m pytest -q
python -m scripts.audit_calculations
```

After downloading licensed labeled photos and configuring weights or an AI vision service:

```bash
export VISION_PROVIDER=nutrilens
export NUTRILENS_WEIGHTS=/models/food_classifier.h5
export NUTRILENS_LABELS=/models/labels.json
python -m scripts.evaluate_photos /data/labels.csv --out results.json
```

`labels.csv` columns: `image_path,true_food_name,true_grams,true_kcal,true_protein`. `image_path` is relative to the CSV. The script explicitly refuses to score unconfigured vision, and **does not credit a default serving size as a photo-derived weight prediction**. It produces per-image outputs and metric coverage; image labels must be harmonized and vetted for leakage before interpreting accuracy. With multi-food images use separate instance/box evaluation.

## Release decision

**NO-GO** on claiming 90% or any other camera-to-nutrition accuracy for the new Reliv implementation. Current status: arithmetic and backend smoke tests pass; photo weighing and independent calorie/protein accuracy remain unvalidated.
