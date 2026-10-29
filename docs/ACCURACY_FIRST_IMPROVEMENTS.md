# Reliv Nutrition AI — accuracy-first improvements backlog

**Living requirements. Not the final deliverable.** The customer scanner and meal diary must remain independent of the admin-learning studio. Mark `[x]` only for implemented/tested engineering, `[ ]` for remaining work. No public market-leadership claims without independent food-photo benchmarks.

## Tier 0 — important customer accuracy and safety

- [x] Track offered/served portion separately from actual eaten portion on generic and mixed plate items.
- [ ] Add grams-left-over and shared-plate split to all meal sources (packaged/restaurant/reference/recipes).
- [ ] Add portion-confidence gates: no fake exact grams from single noncalibrated photo; ask for one meaningful clarification only when necessary.
- [ ] Source-grade per item: exact manufacturer label, lab/official database, verified cooked recipe, or illustrative estimate.
- [ ] Ingredient composition for mixed dishes; cooking oil/ghee, cream, cheese, sauces, bones, peels, and packaging weight must not silently contaminate edible amount.
- [ ] Beverage ice, dilution, sugar syrup and mix-in volume; avoid assuming all beverages are 1g per ml.
- [ ] Recognize unknown/unsupported dish and abstain rather than assign similar-sounding foods and fabricated macros.
- [ ] Detect repeated log by the same user at the same meal/time without blocking intentional re-logs.
- [ ] Account for cooked yield and water loss/gain; raw rice vs cooked rice cannot share a 100g baseline.

## Tier 1 — customer experience and robust everyday tracking

- [ ] Personal bowl/plate/cup size library, optional reference object to make photos more useful for relative portions.
- [ ] 'Yesterday's breakfast again', recurring home recipe, half portion, share portion with another household member.
- [ ] Label/ingredients OCR with user review when GTIN lookup is missing; exact brand, variant, pack size, reformulation date and country.
- [ ] Voice entry (Bengali, Hindi, English, Hinglish), household units, and colloquial dish aliases across regions.
- [ ] Accessibility validation, latency and bandwidth targets, offline meal save with protected retry; server-side photo retention minimization.
- [ ] User can inspect why a number was chosen and fix just one incorrect item, without navigating to the admin site.

## Tier 2 — admin learning, model quality and production

- [ ] Human-review queue sorted by uncertain-but-frequent foods and user complaint frequency (active-learning triage).
- [ ] Flag contradictory annotated weights, duplicate near-identical photos, inconsistent recipes, expired menu references and changed brand labels.
- [ ] Preserve audit/version history for each approved nutrition record; rollback bad edits without rewriting historical logs.
- [ ] Train and evaluate real Indian mixed-plate recognition on rights-cleared, disjoint training/validation/test images, with per-class mAP50/mAP50:95.
- [ ] Run measured 100g versus 300g portion studies on unseen phones, plates, lighting, containers, cooked recipes and cuisine variants. Report gram MAE, MAPE, uncertainty calibration and failure-case coverage.
- [ ] Test protein/kcal error separately from recognition accuracy, each against recorded edible weights and ingredient/label references.
- [ ] Compare head-to-head with real competing apps on identical unseen meals, maintain signed benchmark manifest and prevent holdout contamination.
- [ ] Live backups/restore tests; rate-limits/abuse controls; privacy/deletion and commercial data/model license audit; deployment telemetry, rollback and uptime SLOs.

**Evidence standard:** Single-photo portion mass cannot be claimed exact. Improvements and source-backed records are not themselves camera-accuracy measurements. Benchmarks must never use samples previously exposed through training, admin similarity indexing or tuning in the independent holdout.
