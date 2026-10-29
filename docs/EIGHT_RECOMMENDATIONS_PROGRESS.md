# Eight improvements — living master implementation log

**29 October 2026 · Historical implementation note.** This log documents the eight incremental improvements prior to the final source handoff; see top-level README and `docs/FINAL_RELEASE_VERIFICATION.md` for current release evidence. Original scanner, catalogue, branding/restaurant/USDA options, independent user logging, and admin learning remain available.

**Legend**: `[x]` means that *specific* engineering feature passed local tests; `[ ]` means pending or requires external real-world evidence. Do not equate passing API tests with validated model prediction accuracy.

## 1 · Ingredient-level nutrition and prevention of double counting
- [x] Recipe calculation retains `raw`, `cooked`, or `as_served` per ingredient.
- [x] Roles distinguish prepared dish, independent ingredient, added fat and topping.
- [x] Warnings flag duplicate ingredient IDs/names, possible already-included oil/ghee/sauces, and mixed raw/cooked weight without yield.
- [ ] Train image model to recognize and isolate visible ingredients/condiments in Indian mixed curries/thalis; validate masks, recall and per-item weights.
- [ ] Verify cooking-oil absorption, ingredient cooked yield, bones/peels and density using weighed/ingredient evidence.

## 2 · Smarter portion estimation
- [x] Optional second angle and known plate diameter already accepted by camera API.
- [x] New profile-scoped saved plate dimensions, read/update APIs and compact UI control.
- [x] AI ranges and uncertainty warnings retained; uncertain photos never silently become certified weighed grams.
- [ ] Validate improved weight errors with held-out, physically weighed 100g/300g images across utensils, phone cameras and food types.
- [ ] Multiple plate/bowl/cup profiles and scale-calibrated portion priors.

## 3 · Branded food and nutrition-label reading
- [x] Existing barcode and exact product lookup preserved.
- [x] Optional configured Gemini nutrition-label transcription endpoint; rejects unreadable or incomplete values and requires user review.
- [x] Manual label-entry logging supports per-100g and per-100ml, all four macros and explicit confirmation.
- [x] Optical extraction candidate never gains a verified status from AI transcription alone.
- [ ] Independent OCR benchmark for real Indian packaged food labels and multilingual packaging.
- [ ] Version product labels by country/GTIN/reformulation and compare with manufacturer-issued nutrition documents.

## 4 · Personal meal memory
- [x] Profile-scoped saved food shortcuts; use usual/half/one-and-a-half/double servings.
- [x] Original sourced nutrition status retained; a saved shortcut is not new verified nutrition.
- [ ] Persist and recalculate saved ingredient-based *recipes*, repeat complete mixed-plate meals, store household portion calibration.
- [ ] Secure cloud identity integration and end-user deletion/export options.

## 5 · Better admin learning and conflict detection
- [x] Previously approved examples, revocation, user feedback and separate consent remain protected.
- [x] Admin triage shows most frequently corrected food names and contradictory approved per-100 records by recipe/variant.
- [x] No automatic rewrite of user history or auto-training from unreviewed corrections.
- [ ] Admin model promotion gates, automatic training jobs, experiment lineage, immutable approval trail and rollback of trained weights.
- [ ] Held-out model retraining, true accuracy audit and deployment canary.

## 6 · Accessibility and Hindi/Bengali/Hinglish food recognition
- [x] Conservative multilingual aliases for commonly logged Bengali/Hindi foods; `aloo posto` added as illustrative entry.
- [x] Ambiguous Bengali/Hindi words like `biryani` return multiple varieties, not a wrong default protein choice.
- [x] Optional advanced logging tools collapsed so main user experience remains Scan → Check → Save.
- [ ] Full translated screen labels, voice dictation and independently tested keyboard/screen reader accessibility.
- [ ] Broader regional alias curation without false synonyms or accidental raw-to-cooked substitutions.

## 7 · Nutrition quality/provenance
- [x] Machine-readable source tier and warning on generic catalogue results and normal meal-log responses.
- [x] Manually reviewed package labels carry the `user_label` source rather than manufacturer/lab verification.
- [ ] Consistent evidence objects on every restaurant, barcode, USDA and admin-reference response; version/cite every source record.
- [ ] Validate authoritative Indian cooked-food recipe data; 284 starter values are *illustrative*.

## 8 · Real model performance monitoring
- [x] Admin-only endpoint for evaluation of supplied distinct, held-out test records, with food recognition top-1, gram MAE, kcal MAE, protein MAE and per-group errors.
- [x] Reject non-test split records, duplicate sample IDs and missing/nonnumeric values; detection mAP is explicitly not claimed from classification records.
- [x] Original detector mAP scripts and model evaluation scripts retained.
- [ ] Obtain licensed real Indian meal images, train approved models and run genuinely independent inference benchmarks.
- [ ] Add signed, independent test-set provenance; prevent test images from entering admin similarity index or training.
- [ ] Capture mAP50/mAP50:95, calibration, device-level latency, unknown foods, portion discrimination and cross-cuisine bias.

## Additional improvements worth prioritizing

1. **Edible portion vs packaging and waste**: bones, peels, leftover sauce, shared platters, before-and-after photos. Only ordinary plate-percent portions are covered now.
2. **Measured household units**: each user's specific ladle, tumbler, bowl and roti size, with optional kitchen-scale calibration; distinguish grams from ml by density.
3. **Energy/unit integrity**: prevent kcal-vs-kJ and per-serving-vs-per-100 errors, double counts from toppings, uncooked vs cooked rice mistakes, and product reformulation mismatches.
4. **Safer model abstention**: unfamiliar food, non-food pictures, poor lighting, blur, occluded sauces, mixture of edible/non-edible mass; request one useful clarification rather than guess.
5. **Privacy and ownership**: explicit cloud-photo consent, automatic deletion, data export, deletion, signed access, backups, abuse controls and audit retention.
6. **Offline-friendly diary**: save pending meals encrypted locally, reconcile duplicates and synchronize safely when network returns.
7. **Verified micronutrients only**: show fibre, sodium, added sugars, caffeine and allergens only when exact source records supply them; never infer allergens from images alone.
8. **Continuous comparative benchmark**: same independently weighed meals, matched test conditions and published failure rates for Reliv and competing apps; no unproven “most accurate” claim.

## Verification in this incremental revision

- `python -m pytest -q`: **103 passed**.
- `python -m scripts.audit_calculations`: **11,360/11,360 deterministic scaling checks passed** for **284 illustrative catalogue entries** (10 quantities × 4 nutrients).
- `node --check web/app.js` and `node --check admin/app.js`: syntax passed.
- `python scripts/browser_smoke_mock.py`: desktop/mobile DOM smoke tests passed using **simulated API responses**, including new quick meals/plate/label UI controls.
- No independent food-photo recognition metric, detection mAP, 100g-vs-300g accuracy, calorie MAE, or protein MAE exists for the combined model. The photo-model deployment has **not** been tested on real iOS/Android hardware.

**Do not confuse a tested evaluation *formula* with actual food-photo predictions.** Current production-readiness gate remains FAIL.
