# Reliv Nutrition AI — two-interface, human-reviewed learning system

Status: **work in progress, not final release**. This change is saved in the same `reliv-nutrition-ai` project. A combined archive is intentionally deferred until the owner says **"give the final"**.

## 1. The two experiences

| Interface | Local route | Purpose | Who can act |
|---|---|---|---|
| Customer nutrition website | `/` | Photo scans, mixed meals, food search, nutrition totals, corrections | End user |
| Private admin learning studio | `/admin` | Label photos, annotate individual dishes, enter quantities, approve examples, review corrections, export training data | Administrator with server-configured token |

These are separate HTML/JS interfaces served by the same API. Deploy them on separate admin and user domains via a reverse proxy **after implementing role-based identity and production hardening**. The admin UI never exposes its token to the public user website; it holds the token in current tab memory, not local storage.

To start a protected development setup:

```bash
export RELIV_ADMIN_TOKEN="replace-with-unique-cryptographically-random-secret-at-least-32-characters"
export RELIV_LEARNING_IMAGE_DIR="./private_learning_images"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/admin` and `http://127.0.0.1:8000/`. The public API rejects admin operations when the token is absent/short.

## 2. What "teaching" the AI means

This is **human-in-the-loop supervised data curation + reviewed example retrieval**, not reinforcement learning in the technical sense. There is no automatic online update to neural-network weights. Three distinct operations exist:

1. **Immediate reviewed memory.** Admin takes/owns the food image, enters one or more visible foods, independently records grams, enters calories/protein/carbs/fat from an identified source, and submits the example. A second admin action approves or rejects it. On an identical uploaded photo the user sees approved recorded items and quantities, with warnings to confirm.
2. **Visually close reference.** Near-duplicate hashing may suggest an approved dish. Optional locally staged image embeddings can suggest semantically similar dishes. **Neither method silently transfers weight or asserts calories for an unknown recipe.** The user confirms the dish, variant, cooked portion and any cooking fat.
3. **New trained visual models.** Approved, rights-cleared, labeled examples are exported into grouped train/validation/test splits. Only an explicit separate training job can create a new classifier/detector. Deployment happens after holding out new real-world photo sets and calculating actual metrics.

Every user correction is optional and goes into a separate queue. It cannot automatically overwrite trusted values or become training data.

## 3. Admin annotation instructions

For every image, record:

- A distinct **session/batch group** tying all photos of the same food preparation together to prevent leakage across train/validation/test.
- The **actual dish and recipe variant**, e.g. `Homemade dal tadka with ghee` versus restaurant dal tadka; do not treat the name alone as nutrient identity.
- **Each visible component** separately (e.g. biryani rice, potato, dal, sausages, salad). Draw a bounding rectangle around each food. Multi-food photos lacking complete boxes are excluded from detector training.
- **Edible serving weight in grams** and how obtained: `scale`, `packaging`, or `estimated`. Weights marked `estimated` cannot be used as ground truth in the portion-weight pairing script.
- Nutrient entry basis: values **per 100g** or totals **for the recorded weighed serving**. The server normalizes to values per 100g for consistent scaling.
- Plate diameter only when physically known. A known plate size may help calibration but does not reveal density or hidden food volume by itself.
- Nutrition source (`weighed_recipe`, `packaged_label`, `official_database`, `laboratory`, `estimated_recipe`), evidence link or detailed recipe/measurement notes.
- Ownership/license permission for the photo. Images lacking rights attestation are excluded from public references and training exports.

Example: a food has a **300g weighed edible portion** with **540 kcal and 21g protein for that portion**. Admin selects `total nutrients in weighed serving`, enters 300g, 540 kcal, 21g protein; server saves **180 kcal/100g and 7g protein/100g**. On later confirmation of 100g, the calculator produces 180 kcal/7g; for 300g, 540 kcal/21g. These values are only as valid as the underlying weighed recipe/ingredient information, not a laboratory assay.

## 4. How to collect genuine 100g/300g accuracy ground truth

1. Use a calibrated kitchen scale, tare the plate, weigh 100g of prepared food and photograph it top-down and at ~45°.
2. Separately weigh and photograph 300g of the **same cooked batch**, on a known plate. Keep 100g and 300g as distinct photos within one group.
3. Record the plate diameter, lighting, camera/device, dish identity, mixed components and every cooked serving's ingredient/oil recipe; do not infer edible grams from package weight.
4. Repeat across rice, aloo, dal, biryani, idli, dosa, pizza, pasta, sausages, liquids, packaged foods and mixed thalis; include different cameras/plates/lighting and unseen kitchens/venues.
5. For held-out benchmarking, ensure photos from a particular kitchen batch stay in **one** split. Use new batches/phones for test. **Never train on images that appear in the test set**.

Prepare eligible pairs (does not train or benchmark a mass estimator):

```bash
python -m training.portion_pairs --db nutrition.sqlite3 --out private_training/portion_pairs.csv
```

Only admin examples marked `scale` create eligible pairs, and only different photos with at least a 2.2x weight ratio are paired.

## 5. Export, train, measure

```bash
# Approved and licensed food reference images only. Output path must be empty.
python -m training.export_curated --db nutrition.sqlite3 --output private_training/curated

# Train a classifier (needs TensorFlow and enough real examples per class).
python -m training.train_classifier --data private_training/curated/classification --out artifacts/classifier

# Train a detector (needs Ultralytics and an appropriate license).
python -m training.train_detector --data private_training/curated/detector/data.yaml

# Evaluate near-image reference retrieval on actual held-out admin reference photos.
python -m scripts.evaluate_curated --db nutrition.sqlite3 --split test
```

The exported `classification/train`, `classification/validation`, and `classification/test` folders are grouped. YOLO annotated images and normalized bounding-box label files use the same split. The exporter refuses identical images leaked across different splits. It does not supply model binaries or invent accuracy measurements.

Optional *semantic* candidate search uses a locally installed and separately licensed CLIP-compatible model, not bundled weights:

```bash
# Stage the model locally, review commercial-license terms, and install torch/transformers.
export RELIV_SEMANTIC_MODEL_DIR=/path/to/approved/local/clip-model
python -m training.index_semantic
```

Without a configured semantic model and refreshed index, only exact-image and conservative near-duplicate reference matching operate; it **cannot generalize to every unseen biryani photo**. Cosine similarity is *not* a confidence percentage.

## 6. Validation gates: not all completed

| Gate | Status |
|---|---|
| Admin token fail-closed access | Automated software tests passed |
| Multiple foods / boxes per admin photo | Automated software tests passed |
| Pending → approved → user match | Automated software tests passed |
| Exact-reference 100g/300g recalculation | Automated software tests passed |
| Similar photos never silently inherit grams | Automated software tests passed |
| Optional user feedback / admin review | Automated software tests passed |
| Train/test group and exact-image leak prevention | Automated software tests passed |
| Rights-attested image export | Implemented; independently audited data rights not available |
| Real photo recognition accuracy | **Not measured** |
| Actual detector mAP50 / mAP50:95 | **Not measured** |
| Independent automated gram MAE | **Not measured** |
| Actual calories/protein MAE on weighed Indian meals | **Not measured** |
| Semantic model live inference | **Not tested; optional weights not present** |
| Two-site real browser end-to-end | **Not validated** (local Chromium navigation restricted by execution environment) |
| Production privacy, audit logs, rate limits, role-based identity, deletion compliance | **Pending** |

**Important:** a near-duplicate retrieval test on photos is NOT the same as a food detector mAP score. Admin-selected labels are not objective correctness proof, especially when cooking oil, edible mass and ingredient mix vary. No honest system should show unsupported certainty.

## 7. Security and production requirements

- Deploy admin site behind SSO/RBAC/MFA, HTTPS and allowlisted origins; rotate shared admin bearer token. The present token is for an internal pilot and is not complete production identity management.
- Enforce file lifecycle and authenticated deletion requests, restrict upload and inference rates, cap private storage, and back up encrypted learning files alongside the database.
- Get explicit user permission before submitting photos for review/training; user photo feedback is not automatically training eligible. Avoid storing faces or names in food photos.
- Review image ownership, model license, nutrition data licensing, branding, menu/restaurant nutrition claims and marketing substantiation before launch.
- Test with real Android/iPhone cameras, upload constraints, offline status, failure UX, accessibility, error messages and production monitoring.

## 8. Evidence of current changes

Run `python -m pytest -q` and `python -m scripts.audit_calculations`. The latest development verification ran **81/81 software tests** and **7,720/7,720 arithmetic checks**. The former includes mock images and API flows, not independently labeled Indian food photographs. Real model accuracy, mAP and automatic weight accuracy remain unmeasured.

## 9. Living requirements checklist

For the expanded implementation and open acceptance gates, see [`ADMIN_LEARNING_CHECKLIST.md`](ADMIN_LEARNING_CHECKLIST.md). The protected admin portal also exposes `/api/admin/learning/validation`, which lists available dataset counts and explicitly unresolved image/weight/calorie/protein benchmarks. An administrator **cannot manually mark these scientific gates as passed without data and measured results**.


## 10. October 29 reviewed-correction update — preserves both systems

**User first, admin only on mistakes or new references.** Normal food recognition (when configured), typed-food logs, photo capture, 193 generic food searches, barcode/product matching, restaurant examples, source-backed nutrition calculations and diary tracking remain unchanged. The reviewed reference layer is additional: exact reference photos are recalled; similar photos may offer only candidate dish labels. If neither finds a confident match, the user can search/edit manually without waiting for an admin.

### When an administrator discovers a wrong label or nutrition value

1. Open Admin → **Approved references** and select **Withdraw incorrect reference**, supplying a reason. The bad sample immediately stops appearing in exact/similar reference matching and in the next training export. Historical logs are preserved as originally saved; users can correct their own next entries. The previous record remains in an audit-friendly `revoked` state.
2. If a user submitted a mistake, use **User correction queue**. The attached photo can be viewed only through an authenticated, no-cache admin endpoint. A separate opt-in explicitly controls whether the user allows reuse of the photo as a reference/training example; sharing a photo *only for review* does not grant training rights.
3. For permissioned photos, click **Prepare corrected reference**. The admin input form is pre-filled with the user's *unverified* food name and reported grams only. Calories/protein/carbs/fat are intentionally blank; the administrator must obtain independent recipe/label evidence, check source rights, and submit it for separate approval.
4. After a new sample is approved, the live reference matcher can retrieve it. A truly new model requires a separate dataset export, training and held-out evaluation; user corrections never cause automatic retraining or a false precision claim.

**Limits:** Revocation is a withdrawal/replace workflow, not editing previous users' logs. Exact image matches do not prove that a later meal has the same portion; users still confirm grams. Near-image matches are uncalibrated suggestions, not measured 100g/300g determinations. The README, v0.5 reports, benchmark scripts and earlier checks remain in this same project; no new model-accuracy claim is made.
