> **HISTORICAL v0.2 AUDIT — superseded by [v0.4 release report](RELEASE_REPORT.md). Do not use old counts as current.**

# Reliv Nutrition AI — camera readiness & measured accuracy

**Last checked:** 29 October 2026 (Asia/Kolkata)  
**Release:** v0.2, tested software foundation; NOT a validated nutrition-measurement product.

## Accuracy of this Reliv implementation

| Quality target | Measurement | Result |
| --- | --- | --- |
| 171-food manual search coverage | Food catalogue count | 171 entries; searchable, not camera-recognized |
| Calculation correctness (given source values and grams) | Independent deterministic decimal-rounding audit, 171 × 10 × 4 | 6,840 / 6,840 checks passed |
| API/test behavior | Pytest suite | 16 tests passed |
| Independent food recognition top-1 | Held-out labeled food photographs | **NOT MEASURED** |
| Multi-item detection mAP | Labeled boxes for photographed thalis | **NOT MEASURED** |
| Portion weight error in grams | Photos paired with measured scale weights | **NOT MEASURED** |
| Automatic 100g vs 300g separation | Same-recipe foods weighed 100g and 300g | **NOT MEASURED** |
| Calories and protein prediction MAE | Measured grams + validated recipe composition | **NOT MEASURED** |

**Do not report “90.94% accuracy” as the performance of Reliv.** This number was reported by the independent 22-class [NutriLens](https://github.com/programcode20/NutriLens) project, on its own validation images. [BhojanAI](https://github.com/shreyasvankhede/BhojanAI-IndianFoodCalorieTracker) reports 0.806 mAP@0.5 for 20 detection categories, a different metric. [thejusdutt/nutrilens](https://github.com/thejusdutt/nutrilens) reports 81.1% top-1 on 259 extended Indian images for its own 231-vocabulary setup. These numbers **cannot be averaged or transferred** to Reliv.

## Camera workflow now implemented

- Phone back-camera upload or gallery photo.
- Optional second photograph from a different angle.
- Optional reference plate diameter (20–32 cm choices in UI; API 10–40 cm).
- Gemini multimodal structured output for multiple visible dishes when `VISION_PROVIDER=gemini` and server-side `GEMINI_API_KEY` are set. No key = no AI photo analysis.
- Optional closed-set NutriLens (22 labels), YOLO detector, CLIP adapters with operator-supplied weights/dependencies.
- Unknown/missing foods prompt manual search instead of being silently relabeled as an unrelated dish.
- Per-food estimated grams, range, confidence labels, and required user confirmation. Closed-set classifiers never claim a measured weight.
- Validated manual grams scale the nutrient values; logged meals appear in a daily dashboard.
- `/api/model-info` always returns **null** for unmeasured vision accuracies. `/api/coverage` describes 171 searchable foods and the independent 22-class vocabulary.

## Why exact amount is not guaranteed

Without a calibrated reference, depth, shape and known recipe density, a photo cannot uniquely identify grams. Two identical-looking plates can contain different amounts or hidden ingredients; 100g vs 300g cannot be guaranteed. A **known plate diameter + second angle + ingredient confirmation** are improvements, not a scale substitute.

## Available independent test data

1. **Google Nutrition5k** — 5,006 weighed meals, measured mass, energy, macro values and train/test splits: <https://github.com/google-research-datasets/Nutrition5k>. Large download; cafeteria-biased rather than an Indian-only benchmark.
2. **Indian food image classification datasets** — labeled images (often **without** weighed grams); suitable for recognition but not portion prediction.
3. **New weighed Indian collection required for mass validation:** use 30–50 recipes with 100, 200, 300 g variations, multiple phones and view angles. Split by actual prepared plate/session/person, not by frames of the same plate.

## Instructions for real accuracy computation

1. Supply a licensed, trained model or cloud vision key.
2. Collect legally obtained **held-out** images with `image_path,true_food_name,true_grams,true_kcal,true_protein` columns.
3. Harmonize food names across labels and the 171-entry catalogue.
4. Run `python -m scripts.evaluate_photos /path/to/labels.csv --out /tmp/accuracy.json`.
5. Report sample count, macro F1/top-1 on exactly matching classes, weight MAE (grams) and within-20% rate, and calorie/protein MAE. **Never claim evaluated weight accuracy for default portions.**

## Release verdict

**Ready for prototype website integration and manually-confirmed food tracking. NOT ready to claim independently validated automatic recognition, 100g/300g discrimination, or exact calories/protein.** User confirmation, a live credential, source-verified nutrition data and independent evaluation are required before a production claim.
