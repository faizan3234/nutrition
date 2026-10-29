# Reliv Nutrition AI — expanded food coverage and product improvements

**Living requirements, October 29, 2026. NOT a final release.**

## Verified local implementation in this work-in-progress revision

- 283 searchable *illustrative* generic entries across 18 categories, including **36 desserts**, **15 mocktails**, **26 other drinks**, and **11 fried-rice dishes**.
- Generic snacks/restaurant dishes and extras expanded (e.g., Kolkata biryani, chicken fried rice, chicken lollipop, brownie, cheesecake, falooda, virgin mojito, sugary and sugar-free options, cooking oil, ghee, sauces, and cheese toppings).
- Every generic added entry is `illustrative_starter_not_verified`, **not a validated per-100g nutrition or camera recognition model**. The numbers MUST be replaced with source-backed records before public claims of accuracy. There is no finite list that guarantees recognition of every food.
- For drinks/mocktails the numeric per-100 basis is **per 100 millilitres**, and user-facing portions/logging now show **ml**. Solid foods use **grams**. The legacy API input field is named `grams` even for ml (compatibility); future clients should adopt explicit `amount + unit`.
- Text like "mojito", "virgin mojito", "fried rice", "cheesecake" or "smoothie" requests a variety selection; no unseen recipe is silently assigned.
- Seven new targeted tests pass for catalogue coverage, units, ambiguous choices, and mixed meals. Full suite: **90 passed**; **11,320 deterministic nutrient arithmetic checks passed**. These are NOT real camera/portion/food-composition accuracy tests.

## Additional prioritized living checklist

Legend: [x] code tested locally; [ ] not implemented or not independently validated.

### P0 — must-have for usable and honest nutrition results

- [x] Search by named desserts, mocktails, fried-rice and additional snacks
- [x] Distinct sugary and no-sugar mocktail examples
- [x] Use ml for mocktails and drinks in customer logging and backend receipts
- [x] Require choice for generic food queries that can mean different recipes
- [x] Keep source provenance warning on the expanded demo foods
- [x] Test mixed entry combining food grams and drink millilitres
- [x] Ensure old customer API tests continue passing after expansion
- [ ] Replace every new illustrative recipe nutrient value with audited reference values or properly weighted ingredient recipes
- [ ] Do not compute calories for unknown dishes until the user chooses a reliable food/recipe reference
- [ ] Establish evidence grades: "from pack/menu", "from verified recipe", "estimate", "unknown"
- [ ] For composite meals, separate rice, dal, aloo, protein, pickle, chutney, sauces and toppings; prevent double counting
- [ ] Ask sugar/cream/syrup/ghee/oil and cooking-style questions **only when materially affecting nutrients**
- [ ] Let users select eaten amount in pieces, cups, ladles, rotis, ml, grams, and grams per piece; calibrate these to weighed serving examples
- [ ] Detect unclear meal variety and suggest alternatives rather than forcing a confident wrong label
- [ ] Don't reuse grams from visually similar admin example; use separate weight estimates with user confirmation
- [ ] For beverage cups, distinguish liquid served from ice and container capacity
- [ ] Restaurant brand and menu tracking must not imply restaurant-specific nutrition without published, verified evidence
- [ ] Product variants and reformulations keyed by GTIN/barcode, country, size, date/label photo
- [ ] Store food density if converting ml to g, never assume one-to-one for all liquids
- [ ] Warn on raw-vs-cooked, bone-in-vs-edible weight, dried-vs-boiled, or oil absorbed when those affect nutrition
- [ ] Handle "shared plate" splitting and meal leftovers with before/after photos or direct portion entry
- [ ] Flag implausible nutrient values, duplicate log entries and dietary anomaly boundaries without shaming users

### P1 — practical excellence and low-friction experience

- [ ] Camera guidance: top photo first, optional side angle and reference-size plate for ambiguous foods
- [ ] Auto-sort high/medium/low visual confidence and show correction only for low-confidence items
- [ ] User-friendly "confirm once" interface after recognition; editable portion per item
- [ ] Voice food entry in Hindi, English, Bengali, Hinglish; validate colloquial food names
- [ ] Save user's own recipes, home-cooked dishes, plate/bowl sizes and commonly used brands
- [ ] One-tap "same breakfast as yesterday", "half serving", and "leftovers"
- [ ] Offline queue for saved meals and syncing when online, without leaking private images
- [ ] Show protein, calories, carbs, fats, fibre, added sugars and sodium **only where source fields exist**
- [ ] Clearly distinguish drink sweetness/zero sugar, ice cream scoops, toppings, sauce sides and cooking oil
- [ ] Distinguish nutrition for branded protein shakes by exact variant and container size
- [ ] Explain that official restaurant menus may list *weights* without nutritionally verified macros
- [ ] Food label photo/OCR with user confirmation where online sources are missing or stale
- [ ] Multi-photo fusion with quality checks and graceful fallback to user-entered grams
- [ ] Replace `grams` legacy API name for ml quantities with `amount + unit` via backwards-compatible v2 API
- [ ] Show error-friendly corrections and feedback without sending users to admin screens
- [ ] Customizable food goals without offering medical diagnoses or unsupported personalized targets

### P2 — evidence-based competitive differentiation

- [ ] Establish held-out Indian food dataset covering 100g/300g and mixed plate pairs
- [ ] Validate detector precision/recall and mAP50/mAP50:95 independently, including per-class failures
- [ ] Validate edible-mass MAE, calorie MAE and protein MAE on weighed food
- [ ] Evaluate unseen home-cooked recipes, restaurant varieties, different devices/light and cluttered backgrounds
- [ ] Calibrate probabilities and thresholds on held-out data; test abstention/unknown food rate
- [ ] Compare against competitors with same image/weight ground truth and settings
- [ ] Version approved admin corrections and datasets; isolate holdout examples from training
- [ ] Human review with role-based access, source evidence, consent, data deletion and audit history
- [ ] Safe model rollout: shadow inference, A/B and rollback when held-out metrics degrade
- [ ] Record bias and limitations by Indian region, dish type, portion size and venue
- [ ] Establish production SLOs for camera response, uptime, cost, backup and user data security

**Important:** None of the unchecked items becomes a "passed test" just because a feature is described here. Trained model performance remains **unmeasured** for the Reliv system in this working version.

## October 29 incremental improvement: served versus actually eaten

- [x] Preserve **served amount** and **actually eaten amount** separately for standard food and mixed-plate logs.
- [x] Apply per-item 25%, 50%, 75%, or 100% eaten selections in the customer results screen, defaulting to 100% for existing clients.
- [x] Calculate calories/protein/carbohydrates/fat only for the amount **consumed**, while recording `served_amount` and `consumed_percent` for audit/review.
- [x] Include eaten amount and original served quantity in diary history; preserve legacy clients and old logs through SQLite schema migration.
- [x] 4 targeted automated tests for partial intake, batch mixed intake, invalid ratios, and legacy compatibility.
- [ ] Extend the same eaten-versus-served metadata to restaurant meals, branded packaged products, USDA selections and recipe builder logs.
- [ ] Support user-entered exact grams left over (rather than only 25% steps), shared plates and before/after photos.
- [ ] Run browser/device acceptance for this new selector in real Android/iOS environments.

**Verification at this commit:** `python -m pytest -q` -> 94 passed; `node --check web/app.js` passed; `python -m scripts.audit_calculations` -> 11,320/11,320. These are software and arithmetic checks only; camera nutrition accuracy remains unmeasured. Local loopback browser navigation was blocked by the execution environment in this pass, so no successful browser E2E claim is made.
