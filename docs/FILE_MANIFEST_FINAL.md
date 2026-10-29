# Final source file manifest

**Generated:** 29 October 2026. This list is of packaged files. No private `.env`, SQLite customer histories, training photos, model weights, `.git/` internal objects or external licensed datasets are included.

**Files listed:** 106 (including this index).

## Complete list

- `.env.example`
- `.github/workflows/tests.yml`
- `.gitignore`
- `Dockerfile`
- `LICENSE`
- `README.md`
- `admin/app.js`
- `admin/index.html`
- `app/__init__.py`
- `app/auth.py`
- `app/catalog.py`
- `app/db.py`
- `app/evaluation_monitor.py`
- `app/label_reader.py`
- `app/learning.py`
- `app/learning_monitor.py`
- `app/legacy_adapters.py`
- `app/localization.py`
- `app/main.py`
- `app/packaged.py`
- `app/personalization.py`
- `app/quality.py`
- `app/recipes.py`
- `app/restaurants.py`
- `app/semantic_retrieval.py`
- `app/textlog.py`
- `app/usda.py`
- `app/vision.py`
- `docker-compose.yml`
- `docs/ACCURACY_AND_DATASET_EVIDENCE_v0.5.md`
- `docs/ACCURACY_FIRST_IMPROVEMENTS.md`
- `docs/ADMIN_LEARNING_CHECKLIST.md`
- `docs/ADMIN_LEARNING_GUIDE.md`
- `docs/CAMERA_ACCURACY_AND_RELEASE.md`
- `docs/COMPETITOR_COMPARISON_v0.5.md`
- `docs/DEPLOY_INTEGRATE.md`
- `docs/EIGHT_RECOMMENDATIONS_PROGRESS.md`
- `docs/FINAL_RELEASE_VERIFICATION.md`
- `docs/FOOD_COVERAGE_AND_NEXT_IMPROVEMENTS.md`
- `docs/LIVING_RELEASE_GATE_AUDIT_2026-10-29.json`
- `docs/MASTER_CHECKLIST.md`
- `docs/MODEL_SETUP.md`
- `docs/PRODUCTION_READINESS_v0.5.md`
- `docs/PUBLISH_AND_DEPLOY.md`
- `docs/QA_ARITHMETIC_v0.5.json`
- `docs/QA_BROWSER_v0.5.txt`
- `docs/QA_PYTEST_v0.5.txt`
- `docs/RELEASE_GATE_AUDIT_CURRENT.json`
- `docs/RELEASE_GATE_AUDIT_v0.5.json`
- `docs/RELEASE_REPORT.md`
- `docs/RESTAURANT_AND_BRAND_DATA.md`
- `docs/SUPPORTED_FOODS.csv`
- `docs/SUPPORTED_FOODS.md`
- `docs/VALIDATION_PROTOCOL.md`
- `docs/accuracy_audit_2026-10-29.md`
- `docs/arithmetic_result.json`
- `docs/authorized_foods_example.csv`
- `docs/checklist_status.json`
- `docs/previews/customer_desktop_mock.png`
- `docs/previews/customer_mobile_mock.png`
- `docs/release_metrics.json`
- `docs/source_audit.md`
- `examples/relivpwa_integration.js`
- `requirements-vision.txt`
- `requirements.txt`
- `scripts/audit_calculations.py`
- `scripts/audit_release_gates.py`
- `scripts/browser_smoke_mock.py`
- `scripts/evaluate.py`
- `scripts/evaluate_curated.py`
- `scripts/evaluate_detection.py`
- `scripts/evaluate_photos.py`
- `scripts/generate_food_index.py`
- `scripts/write_master_checklist.py`
- `tests/test_admin_learning.py`
- `tests/test_app.py`
- `tests/test_auth.py`
- `tests/test_batch.py`
- `tests/test_camera_release.py`
- `tests/test_consumed_portions.py`
- `tests/test_deployment_structure.py`
- `tests/test_detection_metrics.py`
- `tests/test_evaluation.py`
- `tests/test_expanded_food_coverage.py`
- `tests/test_improvements.py`
- `tests/test_learning_export.py`
- `tests/test_packaged.py`
- `tests/test_portion_pairs.py`
- `tests/test_restaurant_logging.py`
- `tests/test_restaurants_recipes_text.py`
- `tests/test_training_split.py`
- `tests/test_usda.py`
- `training/README.md`
- `training/export_curated.py`
- `training/index_semantic.py`
- `training/portion_pairs.py`
- `training/split_by_group.py`
- `training/train_classifier.py`
- `training/train_detector.py`
- `web/app.js`
- `web/icon.svg`
- `web/index.html`
- `web/manifest.webmanifest`
- `web/style.css`
- `web/sw.js`
- `docs/FILE_MANIFEST_FINAL.md`

## Primary entry points

- **Detailed README:** `README.md`
- **Final verification evidence:** `docs/FINAL_RELEASE_VERIFICATION.md`
- **Master development checklist:** `docs/MASTER_CHECKLIST.md`
- **Admin learning checklist:** `docs/ADMIN_LEARNING_CHECKLIST.md`
- **Source dataset index:** `docs/SUPPORTED_FOODS.csv` (current food count is 284, verify via `/api/coverage`)
- **Customer UI:** `web/index.html` and `web/app.js`
- **Admin UI:** `admin/index.html` and `admin/app.js`
- **Backend:** `app/main.py`
- **Deployment:** `Dockerfile`, `docker-compose.yml`, `.env.example`
- **GitHub publishing:** `docs/PUBLISH_AND_DEPLOY.md`

All historical v0.5 reports are retained for provenance and do not override the final verification report.
