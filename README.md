# RELIV NUTRITION AI — MASTER HANDOFF

**Unified customer nutrition tracker + private admin learning studio**
**Final consolidated source handoff — 29 October 2026**
**Release:** `0.6.0-source-handoff` · **Status:** Tested software prototype; **not** independently validated for real-world photo-based calorie or portion accuracy; **not cleared for public production**.

This repository contains **one application** with two interfaces:

- **Customer website** at `/`: **Scan → Check → Save**, plus typing, food search, branded/barcode food, restaurant dishes, saved meals, logs and dashboard. Normal logging works even if the admin has never uploaded a reference.
- **Private admin learning studio** at `/admin`: annotate photographs (including multiple foods), enter measured mass and evidence-backed nutrients, approve/revoke records, inspect authorized customer corrections, export training datasets and view quality/validation gaps. This improves the reference library; it does **not** automatically make the model capable of weighing an unseen meal.

The entire prior v0.5 project, historical reports, reference docs, source code, learning features, training/evaluation scripts, tests and checklists are retained here. **Historical reports under `docs/` describe earlier development snapshots** and may mention outdated catalogue/test counts. This README and `docs/FINAL_RELEASE_VERIFICATION.md` are the authoritative statements for this handoff.

## Read this first — what is and is not accomplished

| Capability | Present? | What was verified |
|---|---|---|
| Food search, manual weights, daily totals | Yes | Automated API tests and arithmetic audit |
| Indian, South Indian, Bengali, Western, drinks and desserts | Yes: **284 searchable illustrative catalogue entries** | Search/format tests; **not** 284 trained recognition categories |
| Mixed-food meal logging with individual portions | Yes | API tests; users confirm quantities |
| Mark what was **actually eaten** (e.g. 300 g served, 50% eaten) | Yes | Nutrition correctly uses the confirmed consumed fraction |
| Exact packaged product search / barcode | Integration | Tests use controlled API responses; real products require network and label verification |
| Restaurant names / menu items | Integration | Unverified calories are never represented as official restaurant nutrition |
| Recipe ingredients, cooking-state/added-fat warnings | Yes | Calculation/validation tests; invisible ingredients cannot be recovered from photos |
| Saved plate size and usual meal shortcuts | Yes | API/UI tests; plate diameter alone cannot measure mass |
| Hindi/Bengali/Hinglish food-name aliases | Partial | Selected aliases tested; full localization not complete |
| Customer correction → reviewed admin reference | Yes | Access controls, consent, approval and revocation tested |
| Train/evaluate scripts and group-separated dataset export | Yes | Workflow tests; **no new trained classifier, detector or mass regressor supplied** |
| Two-photo AI scan with configurable provider | Interface and adapter | API/mock tests; real provider inference and phone tests **not** validated |
| Real recognition accuracy, mAP50/mAP50:95 | **UNMEASURED** | No independent held-out inference output exists |
| Automatic 100 g versus 300 g weight accuracy | **UNMEASURED** | No real weighed-photo benchmark exists |
| Real calorie/protein error on meals | **UNMEASURED** | Starter per-100 values are illustrative, not validated food-composition data |
| Fully public production-ready / best-in-market | **No** | See the release blockers below |

**Why the difference matters:** Correct calculation for a manually entered 300 g serving is not proof that a photograph can tell 100 g from 300 g. Nor does a third-party 22-class model's published 90.94% food-name classification result establish accuracy for this application. Do not advertise “most accurate,” “exact calories from a photo,” or “tested on every food.”

## Project layout

```text
reliv-nutrition-ai/
├── README.md                      THIS full setup and operations guide
├── .env.example                   Environment variable template (no secrets)
├── requirements.txt               Core FastAPI server + image handling
├── requirements-vision.txt        Optional local CLIP requirements
├── Dockerfile                     App + customer site + admin site
├── docker-compose.yml             Local-only port, persistent SQLite and learning photos
├── .github/workflows/tests.yml    Automated CI test workflow
├── app/
│   ├── main.py                    Routes, meal logs, photo analysis, admin services
│   ├── catalog.py                 Generic food catalogue (illustrative)
│   ├── vision.py                  Local YOLO, NutriLens & CLIP photo adapters
│   ├── groq_service.py            Groq online nutrition label search & Whisper voice
│   ├── legacy_adapters.py         Operator-supplied NutriLens / YOLO weights
│   ├── learning.py                Reference photos, reviewer approval, revocation
│   ├── learning_monitor.py        Admin correction triage
│   ├── evaluation_monitor.py      Held-out metric calculation with supplied predictions
│   ├── packaged.py                Open Food Facts lookup
│   ├── label_reader.py            Optional label photo extraction
│   ├── restaurants.py             Menu-source rules and estimates
│   ├── recipes.py                 Ingredient-based nutrition calculations
│   ├── usda.py                    USDA FoodData Central adapter
│   ├── personalization.py         Plates and repeat-meal shortcuts
│   ├── localization.py            Indian-language aliases
│   ├── quality.py                 Source-quality labels
│   ├── auth.py                    JWT profile-scoping adapter (not full login)
│   ├── db.py                      SQLite tables and migrations
│   └── textlog.py                 Typed natural-language entry parsing
├── web/                            Mobile-first customer web app/PWA
├── admin/                          Private learning/review interface
├── training/                       Export, splits, classifier/detector training helpers
├── scripts/                        Arithmetic, classification, detection and portion audits
├── tests/                          Software/API/security/deployment-contract tests
├── examples/relivpwa_integration.js Example adapter for existing Reliv PWA
└── docs/                           Full historical reports and latest release evidence
```

See `docs/FILE_MANIFEST_FINAL.md` for a generated, complete file index and `docs/FINAL_RELEASE_VERIFICATION.md` for the actual test commands and outstanding release gates.

## 1. Run locally (Windows, macOS, Linux)

**Requirements:** Python **3.12** recommended, pip, an internet connection for external provider/package lookups. Node.js 22 is used only for JavaScript syntax checks; Docker is optional. **Do not use a public network URL for a demo containing private customer data.**

1. Extract the final ZIP to a folder, open a terminal there, and run:

   **Windows PowerShell**
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt pytest httpx
   Copy-Item .env.example .env
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

   **macOS / Linux**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt pytest httpx
   cp .env.example .env
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

2. Visit **http://127.0.0.1:8000/** (customer), **http://127.0.0.1:8000/admin** (admin), or **http://127.0.0.1:8000/docs** (interactive API docs).
3. With default `.env`, **food search/manual logging works but automatic photo recognition is disabled**. Set up an authorized vision provider below if needed.
4. If the admin screen says it is locked, **generate** an admin token at least 32 random characters long, set `RELIV_ADMIN_TOKEN=...` in `.env`, restart the server and enter it in `/admin`. Never hardcode or publish that token.

**Quick diagnostics**

```bash
python -m pytest -q
python -m scripts.audit_calculations
python -m scripts.audit_release_gates
```

`GET http://127.0.0.1:8000/api/health` should return `ok:true`; `/api/model-info` states which photo model is configured and whether dependencies are present; `/api/coverage` reports the manual catalogue count, not model accuracy.

### Docker on a local machine or test server

```bash
cp .env.example .env             # Windows: copy .env.example .env
# Set RELIV_ADMIN_TOKEN and provider values in .env before starting.
docker compose up --build -d
```

Visit `http://127.0.0.1:8000`. The Docker image **includes `app/`, `web/` and `admin/`** and retains the private learning images with `nutrition.sqlite3` under the named `nutrition_data` volume. The compose port binds only to `127.0.0.1`; configure a properly secured HTTPS reverse proxy before publishing the service. **Docker runtime was not available during this handoff**, so Docker build/start is not certified by the successful source-structure tests.

### Common issues

| Symptom | Cause / action |
|---|---|
| Food scanner says no model | Local vision models require weights in `models/` (e.g. YOLO `models/food_detector.pt` or NutriLens `models/nutrilens.h5`); manual logging remains available |
| Photo fails | Only JPEG/PNG/WEBP up to image limits; check server logs and image format |
| Admin API responds 503 | Admin token missing or shorter than 32 characters |
| Admin page works but cannot approve | Enter the same `RELIV_ADMIN_TOKEN` that was configured on the server |
| User history disappears | Ensure `NUTRITION_DB_PATH` points to persistent disk/volume; don't delete it |
| Barcode search fails | Live Open Food Facts endpoint unavailable, rate-limited or product not indexed |
| USDA search fails | Configure valid `FDC_API_KEY` in server environment |
| Groq search fails | Set `GROQ_API_KEY` in `.env` for online packaged food lookup and voice transcription |
| Mobile camera doesn't open | Use HTTPS on non-localhost mobile browser; grant camera permission |
| Production diary returns 401/503 | Production identity bridge requires correctly signed Reliv JWT and 32+ character `RELIV_AUTH_SECRET` |

## 2. Configure local camera recognition & Groq text/voice

**Zero cloud vision dependencies.** Food photo processing is executed strictly through local models or admin-approved references.

```dotenv
VISION_PROVIDER=auto
NUTRILENS_WEIGHTS=models/nutrilens.h5
NUTRILENS_LABELS=models/nutrilens_labels.json
YOLO_WEIGHTS=models/food_detector.pt

# Optional Groq for online packaged food label search (e.g. Epigamia, Amul Kool) & Whisper voice
GROQ_API_KEY=your_private_groq_key
GROQ_MODEL=groq/compound-mini
GROQ_WHISPER_MODEL=whisper-large-v3-turbo
```

Local vision options:
- `VISION_PROVIDER=auto`: detects locally installed models in priority: YOLO detector → NutriLens classifier → CLIP → none.
- `VISION_PROVIDER=yolo`: local multi-food bounding-box detector (`pip install ultralytics`).
- `VISION_PROVIDER=nutrilens`: 22-class Indian food classifier (`pip install tensorflow`).
- `VISION_PROVIDER=clip`: zero-shot classification (`pip install -r requirements-vision.txt`).
- `VISION_PROVIDER=none`: deliberate camera-model-off mode; manual food searching stays available.

## 3. Customer workflow: Scan → Check → Save

1. Open the customer site on a phone with a secure connection. Tap **Scan**; photograph a meal. Optionally add a second angle and the known plate size to improve estimation context.
2. Check every food candidate in the list: e.g. rice, dal, aloo and sausage as separate items. Correct the name, cooking variant and serving quantity if needed. An uncertain value must be confirmed; the camera does not silently determine exact 100 g/300 g quantities.
3. Choose **how much was actually eaten** (all, 75%, half, 25%). Example: 300 g served, half eaten → record 150 g consumed.
4. Tap **Save**, then review the day's calories, protein, carbohydrates and fat.
5. Under **Other ways to log**, search or type a dish, scan a barcode, choose a restaurant item, search USDA reference foods (if configured), read an exact packaging label (if configured), or save a usual-meal shortcut.

For typed entries, try `100g rice and 200g dal`, `2 idli` or `300ml Coca Cola`. The system asks for a specific pizza/fried-rice/biryani variety when generic wording is ambiguous. A count-only item like `2 idli` may still use a **typical assumed serving size** until confirmed.

For packaged drinks, **grams and millilitres are not interchangeable**; the tracked unit follows the product's verified nutrient basis. For restaurant dishes from Arsalan, Kareem's, Biryani By Kilo and others, a restaurant menu page alone is **not** a caloric/protein label. Only independently reviewed dish/variant nutrition can be called restaurant-specific; generic recipe estimates are opt-in and visibly approximate.

## 4. Admin workflow: improve the knowledge, not interrupt the user

1. Configure your private admin token and open `/admin`.
2. Choose a food photo owned or licensed for this use. For a mixed plate draw **a separate rectangle for each food** and record the dish name, recipe, preparation, plate dimensions, rights and source evidence.
3. If you want training-quality portion data, **tare a kitchen scale** and record the *edible cooked serving mass* (e.g. separately weighed 100 g and 300 g photographs from the same cooked batch). Mark mass basis **`scale`**. Do not mark visual guesses as weighed ground truth.
4. Enter macros **per 100 g** or totals for that **weighed serving**, and source evidence; review and approve. A reviewer approval improves the reference library, but isn't proof of independent nutrient validation.
5. A customer's correction enters a separate **private review queue**. Training reuse requires separate permission; do not train on unreviewed feedback.
6. If an approved example is wrong, **revoke** it. This removes it from new reference results and future training exports without rewriting historical user logs. Add a properly evidenced replacement and approve again.
7. Review frequent mistakes and conflicting recipes under triage. Export the labeled and rights-attested dataset for model training **only after** checking rights, measurement quality and train/test separation.

**Learning behavior:** An **exact** approved photo can recall the corresponding recorded example. A merely **similar-looking** meal is a food/recipe *suggestion*, not proof of the exact recipe, grams, calories or protein. New images generally need real training and evaluation to improve recognition; human corrections do not silently retrain a neural network.

Detailed administrator handbook: `docs/ADMIN_LEARNING_GUIDE.md`. Status and backlog: `docs/ADMIN_LEARNING_CHECKLIST.md`.

## 5. Use verified food data instead of illustrative defaults

The installed generic 284-record catalogue is a **functional demo catalogue**. Its numeric nutrition values have *not* been audited to ICMR–NIN IFCT, INDB or restaurant labels, and must not be claimed as authoritative.

- **Imported verified foods:** Obtain source authorization; prepare a CSV following `docs/authorized_foods_example.csv` (`name,kcal,protein,carbs,fat,default_grams,category,aliases,source`). Numeric macros are **per 100 g**; cooked/raw status and correct variant must be unambiguous. Set `AUTHORIZED_FOOD_CSV` to that local file, then restart the server. A matching name overrides its illustrative record.
- **USDA:** Configure the server-side `FDC_API_KEY` and select the correct preparation/cooking state.
- **Packaged drinks/snacks:** Use the exact GTIN/barcode or a reviewed label image; Open Food Facts can be incomplete or outdated, so compare the source to the package.
- **Restaurant dishes:** Use operator-reviewed CSV following `docs/RESTAURANT_AND_BRAND_DATA.md`. A menu name without nutrient evidence remains an **estimate**.
- **Home/street food:** Prefer an ingredient recipe with weighed raw ingredients, cooking oil and final edible cooked yield. Image analysis alone cannot see hidden fat, sugar or bone weight.

No feature should silently invent nutrient values for unknown foods. The source-quality tier must accompany the result.

## 6. Train or evaluate your own models

This repository supplies **training scripts, not a trained high-accuracy model**. See `training/README.md`, `docs/VALIDATION_PROTOCOL.md` and `docs/ACCURACY_AND_DATASET_EVIDENCE_v0.5.md`.

1. Collect sufficient authorized training images of **distinct** Indian dishes, South Indian foods, street foods, pizzas, pastas, desserts, mocktails, fried rice, fruits and mixed plates; add clear negative/unknown-food samples.
2. Annotate full-plate photos with all food **bounding boxes**, dish names, recipes/variants and region. Pair separate 100 g and 300 g serving photographs with digital-scale measurements, plate size and measured ingredients.
3. Split by **meal batch, kitchen, phone/session and user** so near-duplicates never appear across training/validation/test splits. Hold back a separate final untouched set.
4. Export admin-approved, rights-attested images and grouped metadata:
   ```bash
   python -m training.export_curated --db nutrition.sqlite3 --output private_training/curated
   python -m training.portion_pairs --db nutrition.sqlite3 --out private_training/portion_pairs.csv
   ```
5. Train, only after installing licensed model libraries and collecting enough samples:
   ```bash
   python -m training.train_classifier --data private_training/curated/classification --out artifacts/classifier
   python -m training.train_detector --data private_training/curated/detector/data.yaml
   ```
6. Run actual model predictions on independent photos. Evaluate classification top-1/per-class; detector **mAP50 and mAP50:95**; separately measure **portion mass MAE (g), 100g-vs-300g confusion, calorie MAE (kcal), protein MAE (g), calibration, unknown-food failure rate and latency**.
7. Export a machine-readable report including image IDs, model/checkpoint version, dataset hash/split, run date, sample count and metrics. Never derive “calorie accuracy” by reusing classification scores.

Useful evaluators (require real labeled data and/or real predictions):

```bash
python -m scripts.evaluate_photos /path/to/labeled_images.csv --out real_recognition.json
python -m scripts.evaluate_detection --help
python -m scripts.evaluate /path/to/validation.csv
python -m scripts.evaluate_curated --db nutrition.sqlite3 --split test
```

Check each script's `--help` for its exact input format; they do **not** generate meaningful benchmark percentages without real images/ground truth. The externally available Google Nutrition5k dataset provides measured mass and nutrient labels but doesn't replace a curated Indian-food evaluation dataset.

## 7. API and integration with the existing Reliv PWA

Same server by default: `/` user UI, `/admin` admin UI, `/api/*` shared backend. They can be mapped to **two domains** via an HTTPS reverse proxy only after configuring CORS, identity, access controls and photo privacy. They are not already two independently hosted public websites.

| API | Purpose |
|---|---|
| `GET /api/health`, `/api/model-info`, `/api/coverage` | Readiness, vision configuration, manual catalogue |
| `GET /api/foods?q=dosa` | Generic food search |
| `POST /api/analyze` | Base64 food image(s), optional plate diameter |
| `POST /api/log`, `/api/log/batch`, `GET /api/day`, `DELETE /api/log/{id}` | Meal log/diary/consumed grams |
| `GET /api/products/search`, `/api/products/barcode/{barcode}` | Live packaged food lookup |
| `POST /api/products/label/read`, `/api/products/label/log` | Optional nutrition-label extraction/manual logging |
| `GET /api/restaurants`, `POST /api/restaurants/estimate` | Dish sourcing, opt-in estimate |
| `POST /api/parse-meal`, `/api/recipes/estimate` | Typed meals and ingredient recipes |
| `GET /api/reference-foods` | USDA source lookup when configured |
| `GET/PUT /api/me/plate`, `GET/POST /api/me/shortcuts` | Saved utensils and usual meals |
| `/api/admin/learning/*`, `/api/admin/evaluate/heldout` | Protected moderation, training/export/evidence |

Example photo input (`image_base64` must be a *real* encoded image, not the ellipsis):

```json
{
  "image_base64": "data:image/jpeg;base64,<image content>",
  "secondary_image_base64": null,
  "plate_diameter_cm": 26
}
```

Example *confirmed* food log (select an actual `food_id` obtained from `/api/foods`):

```json
{
  "profile": "demo_user_12345",
  "food_id": "masala-dosa",
  "grams": 300,
  "consumed_percent": 50,
  "meal": "Lunch"
}
```

The profile string is **only a demo identifier** in local mode; it is not authentication. In `RELIV_ENV=production`, private diary endpoints demand a properly signed, scoped short-lived HS256 JWT minted by Reliv's *existing* auth service, with issuer `reliv-auth`, audience `reliv-nutrition` and `sub` equal to the requested profile. `RELIV_AUTH_SECRET` must be at least 32 characters. Public production integration needs a real end-user login, secure cookie/token delivery, HTTPS and the controls below. See `examples/relivpwa_integration.js` and `docs/DEPLOY_INTEGRATE.md`.

## 8. Security, privacy and operational requirements **before public launch**

- **Never deploy in local/demo mode to public internet:** local mode permits diary access by knowing a demo profile identifier.
- Deploy the admin site behind proper **SSO/role-based access/MFA**, network controls and HTTPS; the current long-lived shared token is an internal pilot mechanism only.
- Add request/vision rate limiting, abuse controls, signed photo access, logging without secrets, secure headers, backups, deletion/export requests and privacy/retention processes.
- Back up `nutrition.sqlite3` **and** `private_learning_images/` together. Do not commit photos, trained checkpoints, keys, SQLite user histories or sourced data without rights.
- Use explicit consent before sending photos to cloud AI or reusing them for training; strip non-food personal data and validate dataset licences.
- Validate iOS/Android camera, accessibility, translation, varying bandwidth, low lighting, unknown food and serving-size UX with real users.
- Load test concurrent users and verify production observability, alerting, data migrations, rollback and recovery.
- Confirm the rights to any external models, menu/menu-brand usage and database records. Verify nutrition-value claims and avoid implying medical validation.

These items are **open**, not automatically passed by code tests. Review `docs/PRODUCTION_READINESS_v0.5.md`, `docs/FINAL_RELEASE_VERIFICATION.md` and `docs/MASTER_CHECKLIST.md`.

## 9. Exact release verification

Run:

```bash
python -m pytest -q
python -m scripts.audit_calculations
python -m scripts.audit_release_gates
node --check web/app.js
node --check admin/app.js
```

Current recorded results and caveats are in **`docs/FINAL_RELEASE_VERIFICATION.md`**. Source/test audit does not replace external model evaluation or on-device deployment testing.

### Version and provenance

- **Original project source** is maintained separately from the repositories it was inspired by; source concepts and license notes are in `docs/source_audit.md`.
- Old versioned files such as `docs/RELEASE_GATE_AUDIT_v0.5.json` are retained for traceability, **not** current accuracy claims.
- The final ZIP contains source, docs and tests but intentionally excludes `.env`, user databases, private photos, `.git/`, model weights and unlicensed datasets. A separate Git bundle preserves the original repository history and final handoff commit.
- Deployment and commercial use require project-owner configuration, verified data, licensed models, and real-world testing. **No repository package alone can guarantee exact calories from every food photograph.**

© Reliv Nutrition AI contributors. See `LICENSE` (applies to the project's original code only, not external brands, weights, images or nutrition databases).

## Mixed-plate photo review

The Scan screen now supports up to six user-selected food regions, individual quantity confirmation and explicit matching for ambiguous names. See [Mixed plates, drinks and leftovers](docs/MIXED_PLATE_PHOTOS.md) for examples, API fields and limitations. This is recognition assistance using the configured model, not a newly trained detector or validated photograph-to-weight estimator.
