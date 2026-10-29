# Final consolidated source handoff — verification and remaining gates

**Date:** 29 October 2026  
**Source release:** Reliv Nutrition AI `0.6.0-source-handoff`  
**Bottom line:** Software is runnable and the test suite passes; scientifically measured photo-food accuracy and independent production readiness have **not** been established. “Final” means the entire requested project is packaged together, **not** that every market/ML/clinical gate passed.

## Actual results from the container, not inferred claims

| Test | Result | Interpretation |
|---|---|---|
| `python -m pytest -q` | **106 passed** | API, data validation, security constraints, admin learning, correction, portion consumed, deployment-file contracts. Primarily unit/integration fixtures; no true held-out food images. |
| `python -m scripts.audit_calculations` | **11,360/11,360 passed** across **284 foods × 10 quantities × 4 nutrient fields** | Deterministic per-100g scaling and rounding. Nutrition *source correctness* not checked. |
| `python -m scripts.audit_release_gates` | **production_gate_passed: false** | Reports missing model evidence rather than fabricated accuracy. See `RELEASE_GATE_AUDIT_CURRENT.json`. |
| `node --check web/app.js` and `node --check admin/app.js` | **Both pass** | JavaScript parses; not full application or accessibility certification. |
| `python scripts/browser_smoke_mock.py` | **Desktop and mobile pass** | Browser renders customer app and simulated search/meal/product flows with mocked API data; no real cameras or external services involved. |
| Live local Uvicorn HTTP smoke | **7/7 HTTP routes passed**, admin endpoint fail-closed **503** without secret | `/`, `/admin`, both JS assets, `/api/health`, `/api/coverage`, `/api/model-info` served correctly on localhost. |
| Deployment structure tests | **3 pass**, included in 106 total | Dockerfile includes admin and web, and private learning photos are located under persistent volume. **Docker image not built or run** in this environment. |

## Current real-model accuracy (not available)

| Metric | Verified value | What is needed |
|---|---|---|
| Recognition top-1 / food classifier accuracy | **N/A — not measured** | Download/authorize model; run inference on independent labeled food photos including unknown classes and Indian subgroups |
| Real detector **mAP50**, **mAP50:95** | **N/A — not measured** | Bounding-box ground truth on held-out multi-food plates and real detector predictions |
| Automatic mass error (MAE in grams) | **N/A — not measured** | Kitchen-scale-weighed 100g, 300g, and intermediate real food portions, same/different plates, unseen device/kitchen |
| Accuracy of 100g-vs-300g discrimination | **N/A — not measured** | Independent paired-portions experiment and confusion matrix |
| Calorie error (MAE kcal) | **N/A — not measured** | Real photographed food images with *verified* recipes/ingredient yields, true mass, and model predictions |
| Protein error (MAE g) | **N/A — not measured** | Same as calorie verification, plus reliable nutrient source |
| Nutrition coverage: 284 food entries | **284 manual/searchable starter entries** | Authoritative food-data reconciliation, not 284 tested photo-recognition classes |

The original NutriLens author's 90.94% closed-set classification accuracy is NOT a Reliv benchmark and does not cover weight, kcal or protein. The local CLIP/Gemini/NutriLens/YOLO adapters have **not** been live-validated against independent food photographs during this handoff.

## Functional coverage retained

- Customer Scan → Check → Save and optional search, typed entry, restaurants, barcode, label entry, USDA lookup.
- Mixed plate food-item distinction and **separate confirmed** per-food amounts; actual eaten fraction support on standard and batch logs.
- Plate diameter, optional second photo, meal shortcuts, subset of local-language aliases.
- Private admin annotation, recorded nutrition sources, approvals, reference retrieval, feedback consent, revocation and retraining dataset export.
- Accuracy evaluation *code*, documentation, 284 generic examples and 345-item historical/master engineering checklist, plus separate 126-item admin-learning checklist (overlaps are intentional historical notes).
- All older v0.5 documents and prior test evidence remain for traceability; do not treat old counts as current.

## Open mandatory release blockers

- [ ] Legally licensed and independently tested trained weights/vision service for all required cuisines and unknown-food abstention.
- [ ] Independent held-out multi-food detector and 100g/300g weighed portion evaluation across actual devices.
- [ ] Replace/verify all illustrative nutrient values; restaurant/store recipes and branded drinks require per-variant evidence.
- [ ] Production user identity integrated, MFA/role isolation for admin, security/rate-limit/privacy/retention/backup audits.
- [ ] Real Android/iPhone camera, online API, multilingual accessibility, and production load tests.
- [ ] Controlled comparative accuracy evaluation against competitor apps before any “highest accuracy,” “exact,” or “best in market” marketing claim.

**Decision:** Source handoff **PASS** for runnable code/tests/documentation; independent **production launch and scientific accuracy certification FAIL** (not yet demonstrated). A truthfully labeled beta can be piloted only after appropriate security/privacy controls and informed user consent are addressed.
