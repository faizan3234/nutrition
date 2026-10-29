# Reliv Nutrition AI v0.5 — prioritized production acceptance gates

This release is a **tested software prototype**. Production **FAIL** until every mandatory gate below has evidence.

## What passed
- [x] 193 searchable generic foods with aliases (illustrative numbers)
- [x] Deterministic kcal/protein/carbs/fat quantity math (100g and 300g)
- [x] Source-and-variant-aware packaged product API with incomplete-label refusal (mocked)
- [x] Source-backed Arsalan and Biryani By Kilo menu records, no invented menu macros
- [x] Optional USDA FDC search/logging adapter (mocked, server key required)
- [x] Typed multi-food text parser with ambiguous dish varieties needing confirmation
- [x] Recipe ingredient calculator with optional oil / user-supplied labels / cooked yield
- [x] Mixed food batch logging and atomic insert
- [x] Photo upload, second angle, optional plate diameter
- [x] Deployable optional Gemini/YOLO/NutriLens/CLIP adapters (weights/key NOT bundled)
- [x] Production-mode signed scoped-token checks on private diary endpoints
- [x] Browser DOM smoke with mocked API on desktop and mobile
- [x] Automated tests, CI and Docker environment
- [x] Audit that reports real camera metrics as N/A

## Production blockers — MUST NOT be marked as passed
- [ ] Train or lawfully license a calibrated food recognition model
- [ ] Collect separate, real held-out photo labels and execute end-to-end top-1 accuracy
- [ ] Annotate actual mixed plates and execute real detection mAP50 and mAP50:95
- [ ] Conduct 100g-vs-300g camera test with kitchen scale and matched dish/plate conditions
- [ ] Validate mean absolute edible-gram error on independent dishes
- [ ] Validate calorie and protein MAE against weighed/lab or recipe references
- [ ] Validate unknown/ambiguous food rejection and failure handling
- [ ] Replace illustrative catalogue rows with appropriate licensed sourced records
- [ ] Verify menus/product labels and their commercial reuse rights and update cadences
- [ ] Configure actual Gemini or deployed local model, run live API inference
- [ ] Configure and test live Open Food Facts lookup with rate limits
- [ ] Configure and test live USDA FDC with own API key
- [ ] Integrate PWA authenticated identity, server secrets, expiry, and account recovery
- [ ] Security review for photo upload, prompt injection, authentication, authorization, cookies and CORS
- [ ] Privacy policy: consent, photo retention, account deletion, data export
- [ ] Mobile QA on actual iPhone/Android browsers and low-end devices
- [ ] Accessibility, performance, latency/cost and offline-mode tests
- [ ] Monitoring/error reporting, backups/restore, rollout and rollback, disaster recovery
- [ ] Independent head-to-head comparative study against competitors on same weighed meals
- [ ] Legal substantiation and approval for any superlative accuracy claims

## Model acceptance metrics before go-live

- Top-1 accuracy, macro-averaged recall/F1 and per-category confusion matrices on independent Indian and global foods.
- For detection: mAP50, mAP50:95, class AP, false positives per plate, recall for rare foods and unknown rejection.
- For mass: gram MAE, median error, MAPE excluding zero-mass references, separately for 100g vs 300g pairs.
- For kcal/protein: MAE/MAPE, ±10/20% tolerance hit rate, rates of missing/abstained cases; quantify oil/recipe uncertainty.
- Also track: photo/manual correction rate, 95th percentile latency, model and API cost per scan, usability and barcode exact-match coverage.

Never conflate testing the metric computation code with measurement of actual model accuracy.
