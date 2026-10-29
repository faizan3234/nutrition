# Reliv Nutrition AI — Evidence-based master checklist

**Status: 171 implemented checks; 158 pending items; 329 total**.

Checked means the relevant implementation exists and passed software-level checks when applicable.
It does NOT mean independently measured camera accuracy, commercial readiness, or clinical validation.
No external dataset or trained model may be marked completed without saved evidence.

## Highest-priority blockers

1. Acquire lawful image datasets and pre-trained weights; execute GPU training and inference.
2. Weigh real Indian mixed meals and evaluate photo-predicted grams, calories, protein and mAP.
3. Replace illustrative food nutritional values with verified licensed food composition data.
4. Authenticate users; enforce security, consent, retention and product data licensing.
5. Test deployed site on actual Android/iPhone cameras, then compare against competitors.

## 01 · Repository & architecture

- [x] Modular FastAPI application
- [x] Independent food catalogue module
- [x] Vision model adapter abstraction
- [x] Nutrition calculation module
- [x] SQLite persistence module
- [x] Local mobile website
- [x] PWA install manifest
- [x] Offline static asset service worker
- [x] Docker container recipe
- [x] Docker Compose local persistence
- [x] GitHub Actions automated test workflow
- [x] Dependencies separated for core/vision
- [ ] Create brand-new remote GitHub repository
- [ ] Publish verified tagged production release
- [ ] Set up staged deployment environments

## 02 · Indian and international food coverage

- [x] North Indian food examples
- [x] South Indian food examples
- [x] Bengali/East Indian examples
- [x] West Indian examples
- [x] Rice and biryani examples
- [x] Pizza examples
- [x] Pasta examples
- [x] Noodle and Asian examples
- [x] Fast food and snacks examples
- [x] Sausage and egg examples
- [x] Fruit and nuts examples
- [x] Drinks and generic shake examples
- [x] Aliases for many spelling variants
- [x] Complete searchable food CSV export
- [ ] Validate every recipe against licensed reference data
- [ ] Independently test each catalogue food in camera photos
- [ ] Integrate multilingual Hindi food name synonyms
- [ ] Integrate multilingual Bengali food name synonyms
- [ ] Create region-specific recipe variants
- [ ] Measure out-of-distribution unknown-food rejection

## 03 · Packaged food / beverage lookup

- [x] Open Food Facts integration module
- [x] Barcode format validation
- [x] Per-100 nutrition label normalization
- [x] Volume-versus-mass unit selection
- [x] Reject incomplete nutrition labels
- [x] Prevent NaN/negative nutrient values
- [x] Packaged product search endpoint
- [x] Packaged product barcode endpoint
- [x] Packaged product logging endpoint
- [x] Product source attribution in API
- [x] Mocked cola 100ml versus 300ml arithmetic test
- [x] Mocked branded protein-shake 100ml versus 300ml test
- [x] Client-side branded product search UI
- [x] Client-side barcode-entry UI
- [x] Optional browser barcode-camera workflow
- [ ] Validate real Open Food Facts network integration
- [ ] Verify Coca-Cola regional SKUs against photographed labels
- [ ] Verify Epigamia variant labels against actual packaging
- [ ] Implement product-specific serving size suggestions
- [ ] Implement package nutrition label OCR and user correction
- [ ] Set API rate limits/caching policy with provider
- [ ] Create verified Indian branded-products QA sample

## 04 · Photograph capture

- [x] Phone photo file input
- [x] JPEG/PNG/WEBP validation
- [x] EXIF orientation handling
- [x] Large image dimension limit
- [x] Upload byte-size limit
- [x] Optional second-camera-angle input
- [x] Known plate diameter entry
- [x] Second photo included in vision request
- [x] Photo preview in website
- [x] Explicit user-triggered photo upload
- [ ] Actual Android Chrome camera test
- [ ] Actual iOS Safari camera test
- [ ] Unsupported camera/device fallback QA
- [ ] Low-light and glare image QA
- [ ] Photo retention policy and deletion compliance
- [ ] Accessibility review of capture experience

## 05 · Food recognition

- [x] Configurable Gemini adapter
- [x] Configurable CLIP adapter
- [x] Operator-supplied NutriLens 22-label adapter
- [x] Operator-supplied YOLO detector adapter
- [x] No fabricated closed-set weight output
- [x] Unmatched dish flagged for correction
- [x] Camera provider readiness API
- [x] Recognized food matched conservatively
- [ ] Acquire legally usable food detector model weights
- [ ] Acquire legally usable Indian food classifier weights
- [ ] Train on a licensed Indian food image dataset
- [ ] Train on mixed Indian thali images
- [ ] Benchmark top-1 classification accuracy
- [ ] Benchmark top-5 classification accuracy
- [ ] Evaluate per-class confusion and unknown food
- [ ] Benchmark performance on global foods
- [ ] Measure real mixed-plate mAP@0.50
- [ ] Measure real mixed-plate mAP@0.50:0.95
- [ ] Cross-test unseen phones and locations
- [ ] Choose best model using held-out evidence

## 06 · Portion and food mass

- [x] User-entered grams supported
- [x] Optional plate-size parameter in AI prompt
- [x] Optional second view in AI prompt
- [x] Report AI weight as estimate not scale measurement
- [x] Return uncertainty ranges if inferred
- [x] Fallback default serving explicitly labeled
- [x] Never return a measured-mass flag for a photograph
- [ ] Train mass regressor with measured gram labels
- [ ] Use Nutrition5k held-out mass ground truth
- [ ] Create Indian weighed meal benchmark
- [ ] Physical plate calibration validation
- [ ] Measure 100g versus 300g classification performance
- [ ] Test overlapped items separately
- [ ] Test liquid volume in transparent containers
- [ ] Test thick curry under opaque sauce
- [ ] Test bowl depth and occlusion
- [ ] Quantify gram MAE and error intervals
- [ ] Determine worst-case underestimation rate
- [ ] Benchmark against digital kitchen scale readings
- [ ] Test 10 kitchen lighting conditions

## 07 · Nutrition provenance and formulas

- [x] Decimal half-up per-100 serving arithmetic
- [x] Calories formula scales with amount
- [x] Protein formula scales with amount
- [x] Carbohydrate formula scales with amount
- [x] Fat formula scales with amount
- [x] Precision and rounding regression tests
- [x] Food source field in API
- [x] Optional source-attributed replacement CSV
- [x] Validate imported CSV numeric ranges
- [ ] License and import IFCT values
- [ ] License and import INDB recipe values
- [ ] Use USDA FDC CC0 for non-Indian reference items
- [ ] Version each source dataset
- [ ] Trace macros to recipes/ingredients
- [ ] Validate recipe oil and ghee variation
- [ ] Validate cooked versus raw weight basis
- [ ] Validate food density across recipe variations
- [ ] Test calorie versus label values
- [ ] Test protein versus laboratory/reference labels
- [ ] Measure calibration of uncertainty estimates

## 08 · Meal diary and dashboard

- [x] Save manual food log
- [x] Save packaged food log
- [x] Save 2–12 mixed-plate components atomically
- [x] Read daily diary
- [x] Remove food log
- [x] Calculate daily calories
- [x] Calculate daily protein
- [x] Calculate daily carbohydrates
- [x] Calculate daily fat
- [x] Show editable portion fields
- [x] Set daily calorie goal
- [x] Set daily protein goal
- [x] Group foods by breakfast/lunch/dinner/snacks
- [x] Store source and quantity unit
- [ ] Add verified account authentication
- [ ] Sync food history with existing Reliv user accounts
- [ ] User-controlled photo deletion
- [ ] Export diary as JSON or CSV
- [ ] Handle travel between timezones accurately
- [ ] Dietitian-reviewed goal guidance

## 09 · Browser and device quality

- [x] Frontend JavaScript syntax check
- [x] Browser DOM smoke test using mocked API responses
- [x] Client HTML input constraints
- [x] Mobile layout CSS
- [x] Food search result DOM rendering
- [x] Branded search result DOM rendering
- [x] Barcode fallback manual entry
- [x] Status display for unavailable camera provider
- [x] Disable unfinished product labels from logging
- [ ] End-to-end browser automation on served URL
- [ ] Android real-device smoke test
- [ ] iPhone real-device smoke test
- [ ] Screen reader usability check
- [ ] Voice input and speech feedback
- [ ] Test offline-to-online reconnection
- [ ] Performance test on low-end Android phones
- [ ] Accessibility WCAG audit

## 10 · Unit and integration tests

- [x] FastAPI health test
- [x] Food coverage test
- [x] 100g versus 300g nutrient test
- [x] Invalid serving input test
- [x] Mixed plate batch logging test
- [x] Batch atomicity test
- [x] Batch size constraint test
- [x] Branded product normalization test
- [x] Branded product incomplete-nutrients test
- [x] Barcode input validation test
- [x] Packaged food logging integration test
- [x] Packaged search mock test
- [x] No-vision provider explicit status test
- [x] Two-photo API payload test
- [x] Fake unmatched food not given nutrients
- [x] IoU geometry unit test
- [x] mAP perfect-prediction fixture test
- [x] mAP wrong-class fixture test
- [x] mAP false-positive fixture test
- [x] Group-wise train/validation/test split leak test
- [x] Deterministic split test
- [x] Full nutrition-arithmetic catalogue check
- [ ] Live Gemini integration test using real API key
- [ ] Live YOLO weights inference test
- [ ] Live NutriLens H5 inference test
- [ ] Live Open Food Facts integration test
- [ ] Camera pipeline performance load test
- [ ] API access-control penetration tests
- [ ] Automated UI screenshot acceptance test

## 11 · Benchmark design

- [x] Separate classification and nutrient accuracy metrics
- [x] Photo benchmark runner
- [x] Mixed-plate mAP metric runner
- [x] Calories MAE metric runner
- [x] Protein MAE metric runner
- [x] Gram MAE metric runner
- [x] Train/validation/test split manifest tool
- [x] No fabricated model scores
- [x] No copied upstream accuracy claims
- [ ] Download licensed Indian image training images
- [ ] Download Nutrition5k mass-labeled photos
- [ ] Run Indian dish holdout inference
- [ ] Run mixed thali holdout inference
- [ ] Run model mass regression inference
- [ ] Run calories/protein ground truth evaluation
- [ ] Calculate 95% confidence intervals
- [ ] Test worst-case tail error
- [ ] Run independent unseen-device validation
- [ ] Publish model card and per-class results
- [ ] External replication of accuracy report

## 12 · Training and optimization

- [x] Classifier transfer-learning script
- [x] Multi-food detector training script
- [x] Fixed random seed options
- [x] Early stopping and validation checkpoint
- [ ] Run GPU classifier training
- [ ] Run GPU detection training
- [ ] Improve poor minority-food classes
- [ ] Perform class-balanced augmentation
- [ ] Run food-specific segmentation training
- [ ] Train ingredient composition estimator
- [ ] Train portion/mass estimator
- [ ] Tune confidence thresholds on validation set
- [ ] Temperature-scale model confidence
- [ ] Benchmark ensemble versus best single model
- [ ] Quantize model after accuracy checks
- [ ] Benchmark edge-device latency
- [ ] Measure cost per 1,000 scans
- [ ] Document reproducible hardware and training duration

## 13 · Security, privacy, and compliance

- [x] Server-side private AI key only
- [x] No camera upload until user action
- [x] Reject malformed base64 images
- [x] Limit image pixels and bytes
- [x] Protect API errors from echoing secrets
- [x] Use parameterized SQLite queries
- [x] Use exact barcode format validation
- [x] Block incomplete community product labels
- [ ] Real login / authorization for diary records
- [ ] Production rate limiting
- [ ] TLS and secure origin end-to-end
- [ ] Camera/photo privacy notice and consent
- [ ] Photo deletion and retention jobs
- [ ] Terms and privacy policy review
- [ ] Threat model for user-uploaded photos
- [ ] AI prompt-injection regression testing
- [ ] Account deletion request implementation
- [ ] Healthcare compliance/legal review
- [ ] Third-party image model license review
- [ ] Third-party dataset use rights review
- [ ] Open Food Facts attribution and ODbL audit

## 14 · Deployment and release

- [x] Docker configuration
- [x] Environment example
- [x] Local database persistence option
- [x] PWA client SDK example
- [x] API documentation via FastAPI OpenAPI
- [x] Source repo commits prepared
- [x] Food catalogue exported for download
- [ ] Configure deployed vision key or licensed weights
- [ ] Run live smoke tests on hosted site
- [ ] Connect secure Reliv authentication
- [ ] Attach PWA Nutrition tab in existing repository
- [ ] Set database backups
- [ ] Set error tracking and budget alarms
- [ ] Enable production metrics
- [ ] Create new GitHub remote repository
- [ ] Push source to newly created remote repository
- [ ] Deploy staging instance
- [ ] Deploy production instance
- [ ] Rotate production API credentials

## 15 · Market-leading accuracy claims

- [x] No unsupported market-superiority claim
- [x] Accuracy report distinguishes tests from camera benchmarks
- [ ] Benchmark against at least 3 competing systems
- [ ] Obtain written repeatable evaluation protocol
- [ ] Demonstrate superiority on Indian dishes
- [ ] Demonstrate superiority on mixed plates
- [ ] Demonstrate superiority for 100g versus 300g
- [ ] Demonstrate superiority for branded food lookup
- [ ] Independent study with confidence intervals
- [ ] Publish methods and calibration plots
- [ ] Obtain reviewer/dietitian validation
- [ ] Legal marketing claim review

## Test evidence

- `python -m pytest -q` — API, math, product-label, batch, metadata and evaluation-tool tests.
- `python -m scripts.audit_calculations` — current catalogue × ten masses × four macros.
- `node --check web/app.js` — static JS parser check.
- `python -m scripts.evaluate_detection --ground-truth ... --predictions ...` — real mAP, requires actual annotations and predictions.
- `python -m scripts.evaluate_photos ...` — real single-food photo tests, requires operator-supplied model and labeled photos.
- `python -m scripts.evaluate ...` — gram/kcal/protein MAE, requires independent weighed meals.
- Synthetic unit-test fixtures are not a genuine model benchmark.

### Unsupported marketing statements

Do not claim **most accurate**, **highest mAP**, **exact food weight from one photograph**, **lab-verified nutrients**, **all foods automatically recognized**, or **best in the market** without an independent market comparison and measured validation.


## 17 · Source-backed branded / restaurant / text and recipe expansion (v0.5)

- [x] Official-menu provenance: Arsalan menu entries
- [x] Official-menu provenance: Biryani By Kilo entries
- [x] Refuse brand-specific macros without verified nutritional evidence
- [x] Show restaurant advertised package size separately from edible consumed weight
- [x] Support opt-in generic restaurant recipe estimates
- [x] Retain restaurant attribution and estimate source in diary
- [x] Operator-reviewed restaurant nutrition CSV integration
- [x] Typed entry parses explicit 100g vs 300g amounts
- [x] Typed entry identifies brand name without pretending to know barcode
- [x] Detect ambiguous generic pizza/pasta varieties and require selection
- [x] Support simple piece count with explicit typical-portion assumption
- [x] Split comma/and-separated meal descriptions into multiple food suggestions
- [x] USDA FoodData Central search and reference-food logging adapters
- [x] Reject incomplete USDA macro records
- [x] Recipe builder calculates weighed ingredient totals and cooked yield
- [x] Permit addition of oil/ghee via explicit labeled ingredient nutrition
- [x] Server-side token signature, expiry, audience and profile checks for production diary
- [x] Production mode fails closed when auth secret is missing
- [x] Restaurant, text and USDA website mock smoke tests on mobile and desktop
- [x] Reproducible release audit indicates unmeasured real-food benchmarks
- [x] Competitor comparison and sourced restaurant-data policy
- [ ] Obtain verified official Kareem's menu item and nutrient facts
- [ ] Independently verify each restaurant nutrition CSV row with manufacturer/restaurant
- [ ] Import all 193 starter nutrition entries from licensed reference sources
- [ ] Execute live USDA and OFF requests after operator configures service credentials/network
- [ ] Verify current India-specific Coke and Epigamia package variants and contents
- [ ] Verify accurate per-100ml values where density and labeling conventions differ
- [ ] Train and calibrate a photo model for 193 dishes and unknown-food rejection
- [ ] Run real Indian mixed-plate object detection mAP test
- [ ] Run actual 100g/300g photograph discrimination study with weighed meals
- [ ] Audit separate vessel sizes, food depth, plate placement and camera distortion
- [ ] Add dataset consent/PII redaction and commercial licensing records
- [ ] Conduct API abuse/load and independent penetration tests
- [ ] Integrate actual Reliv PWA JWT issuer, identity lifecycle and data export/deletion
- [ ] Launch trusted menu/nutrition refresh process and stale data detection
- [ ] Real Android/iPhone/camera/low-light/low-network QA
- [ ] Run an independent competitor head-to-head at identical meal/label conditions
- [ ] Document independently verified recognition accuracy, mAP50 and mAP50:95
- [ ] Document independently verified gram/kcal/protein MAE and confidence intervals
- [ ] Obtain legal evidence approval for any market-leading accuracy superlative


## Later incremental scope — not included in the legacy 329-item count above

The food coverage, mocktails, desserts, fried rice, ingredient variants, and advanced product logic are tracked in [FOOD_COVERAGE_AND_NEXT_IMPROVEMENTS.md](FOOD_COVERAGE_AND_NEXT_IMPROVEMENTS.md). Its checked items are test-backed implementation only; its pending items remain release blockers or product-improvement targets. When the user asks for the final unified release, reconcile the legacy engineering, admin-learning and food-coverage checklist counts into one deduplicated master checklist.


---
## Incremental eight-improvement checklist · October 29, 2026 (non-final)

See [`EIGHT_RECOMMENDATIONS_PROGRESS.md`](EIGHT_RECOMMENDATIONS_PROGRESS.md) for item-by-item evidence, tested engineering additions, and open scientific gates. These incremental items supplement, not replace, the original 329-item v0.5 backlog.

- [x] Warn when a prepared dish and added oil/cheese could double count nutrition.
- [x] Label raw/cooked ingredient weight basis and flag mixed measurements without yield.
- [x] Save a user's known plate diameter while warning it is not a weighing scale.
- [x] Save user-specific meal shortcuts and log half/usual/double amounts.
- [x] Read package labels optionally with configured AI; require explicit label review; support manual per-100g/ml labels.
- [x] Add limited conservative Bengali/Hindi/Hinglish aliases and preserve ambiguous-dish choices.
- [x] Add admin triage ranking frequently corrected foods and conflicting approved nutrition entries.
- [x] Expose source-quality labels for generic foods and user-typed package labels.
- [x] Evaluate supplied held-out samples only; report top-1 and MAE separately; never claim missing mAP.
- [x] Hide advanced user entry behind optional disclosure; desktop/mobile mock browser tests passed.
- [ ] Independently benchmark real photo recognition, detector mAP50 and mAP50:95 with licensed held-out images.
- [ ] Independently benchmark 100g/300g discrimination, weight MAE, kcal MAE and protein MAE.
- [ ] Train/validate model weights before promoting to live camera scanning.
- [ ] Replace 284 illustrative starter foods with source-verified Indian composition/recipe datasets.
- [ ] Extend end-to-end nutritional evidence and actual eaten-portion handling to all log types.
- [ ] Verify live Android/iPhone capture, label OCR quality, app security, source licenses and production SLOs.
