# Model and licensed-data setup

Reliv is independent code that implements a common API for multiple food-recognition techniques. **It does not copy or relicense any upstream AI weights, model source or image datasets.** Inspect all upstream model and dataset licenses before commercial use.

## Recommended open-vocabulary camera mode

Server-side `VISION_PROVIDER=gemini`, `GEMINI_API_KEY=...`, optionally `GEMINI_MODEL=...`; photo recognition requires Internet and is subject to Google model availability, data practices and costs. Verify output against weighed portions. The published code does not establish recognition, portion or calorie accuracy for this provider.

## Optional original 22-class Indian classifier

Original code and model: <https://github.com/programcode20/NutriLens>. Their README advertises MIT but as of this audit a standalone LICENSE file was not found. **Confirm permission before copying, bundling or commercially hosting their model.** For authorized operator-supplied weights:

- put H5 at `models/nutrilens.h5` and original labels at `models/nutrilens_labels.json`,
- install TensorFlow compatible with that model,
- set `VISION_PROVIDER=nutrilens`.

This produces **one class label only**. Its output does NOT distinguish 100g and 300g.

## Optional multi-item detector

Original concept: <https://github.com/shreyasvankhede/BhojanAI-IndianFoodCalorieTracker>. The repo contains `model/food_model.pt`. Confirm the model permissions and Ultralytics AGPL/commercial implications before deployment. Supply licensed weights at `models/food_detector.pt`, install `ultralytics` and set `VISION_PROVIDER=yolo`. This produces item bounding-box classes **without actual grams**.

## Optional general classifier

`VISION_PROVIDER=clip` with packages in `requirements-vision.txt` performs an unverified single-image top-1 match over the starter catalogue; it does not estimate grams.

## Original literature and approaches

- DietAI24, RAG food inference / weight estimation research: <https://github.com/Runz96/DietAI24>. Its numerical findings are not inherited by Reliv.
- FoodAnalyser × Fit, IFCT/INDB-first lookup and daily-tracker design: <https://github.com/suvamneog/foodAnalyser-v2>. We do not copy its recipes or database without independently verifying licensing.
- Nutrition5k 5,006 measured meals: <https://github.com/google-research-datasets/Nutrition5k>.

## Source-backed nutrition

Starter records are explicitly marked `illustrative_starter_not_verified`. After obtaining legal usage rights to authoritative values, provide a CSV with `name,kcal,protein,carbs,fat,default_grams,category,aliases,source`, then set `AUTHORIZED_FOOD_CSV=path/to/values.csv`. Same-named rows override demo values. All numbers must be **per 100g**. See `docs/authorized_foods_example.csv`.
