# Competitor analysis — sourced, dated October 29, 2026

**Do not borrow any other company's accuracy numbers or assert comparative superiority** unless Reliv has independently run the same held-out meals under the same protocol.

| Competitor | Verified published feature | Lessons for Reliv | Source |
|---|---|---|---|
| MyFitnessPal | Premium Meal Scan suggests foods from a photograph, with user selection and serving adjustments | Multi-food recognition and quick manual correction are table-stakes; not unique | https://support.myfitnesspal.com/hc/en-us/articles/360045761612-How-to-use-the-Meal-Scanner |
| Cronometer | Curated nutritional records and reviewed branded labels, USDA/NCCDB sources | Source provenance and verification matter as much as vision | https://support.cronometer.com/hc/en-us/articles/360018239472-Data-Sources |
| SnapCalorie | Photo-based calorie estimates; acknowledges image ambiguity for ingredients/oil; reports an error figure in its own materials | Test in real conditions; hidden oils and bowls remain key challenges | https://www3.snapcalorie.com/faq.html |
| Reliv Nutrition AI v0.5 | 193 generic search entries, source-backed restaurant menu listings, OFF product lookup, optional USDA reference records, user-confirmed photo providers | No independent food-photo accuracy or commercial benchmarking yet | This repository's source and tests |

**Genuine possible differentiation:** Bengali/South Indian and mixed-thali vocabulary, restaurant-specific attribution and honest fallback, typed foods and quantity, second-angle capture, plate reference, explicit confidence/measurement labels, optional offline-first Reliv PWA integration, provenance for each entry. These are product design goals/capabilities, NOT proof of being better than competitors.

## Minimum fair comparative study

1. Fix versions and pricing of each app under comparison.
2. Recruit independent evaluators; blind ground-truth labels and app identities where feasible.
3. Use the SAME weighed meal set: at least 100 Indian meals across homemade, street, restaurant, regional, and packaged; include 100g and 300g matched dishes with identical plates.
4. Capture photographs on the SAME phone under the same lighting and angles.
5. Report independently: recognized exact food, count/instance detection mAP50 and mAP50-95, edible mass MAE, calories MAE/MAPE, protein MAE, incomplete/rejected cases, correction time, and data source coverage.
6. Do not use training or calibration meals in the held-out test set. Prefer dish/restaurant-disjoint splits and record confidence intervals.
7. Publish all test cases, false matches, source labels, model configs, benchmark scripts and limitations.

**No competitor head-to-head was performed in this release.**
