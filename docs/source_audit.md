# Source audit — 29 October 2026

The new implementation is original. We did not copy source code, model weights,
training data or nutritional datasets from the projects below.

| Project | Useful idea | Verified limitation | License note |
|---|---|---|---|
| [programcode20/NutriLens](https://github.com/programcode20/NutriLens) | Indian EfficientNet classifier (22 categories), grams editor, barcode and history | 90.94% **reported classification** accuracy does not assess weight or nutrient accuracy; depth notebook not integrated in main app | README says MIT, but root LICENSE was not found; clearance needed before copying |
| [shreyasvankhede/BhojanAI](https://github.com/shreyasvankhede/BhojanAI-IndianFoodCalorieTracker) | YOLOv8 multi-item bounding boxes, fuzzy search and historical data | 20 classes, reported 0.806 mAP@0.5; requires user-provided amount | LICENSE not found; Ultralytics packages may require AGPL compliance/commercial terms |
| [Runz96/DietAI24](https://github.com/Runz96/DietAI24) | Food-code and portion retrieval research | Evaluation targets ASA24 and Nutrition5k, not a general Indian food benchmark | README says MIT, but no root LICENSE found |
| [suvamneog/foodAnalyser-v2](https://github.com/suvamneog/foodAnalyser-v2) | Full-stack food analysis/tracking UX | No independent calorie/portion validation completed | Verify before reuse |
| [google-research-datasets/Nutrition5k](https://github.com/google-research-datasets/Nutrition5k) | Weighed meals with protein/macros and predefined splits | Western cafeteria bias, requires large data downloads | Dataset CC BY 4.0; attribution required |

Official nutrition sources to assess: [ICMR–NIN IFCT 2017](https://www.nin.res.in/ebooks/IFCT2017.pdf) and the [Indian Nutrient Databank](https://www.anuvaad.org.in/indian-nutrient-databank/). IFCT largely describes raw ingredients, not arbitrary cooked dishes. Check permissions for bulk data reuse and record recipe provenance.

**No independent validation establishes that the new project is more accurate than its references.** Accuracy requires weighing and photographing real dishes and measuring errors with a held-out test set.
