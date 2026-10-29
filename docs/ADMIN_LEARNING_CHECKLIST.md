# Reliv Nutrition AI — living admin-learning checklist

This checklist tracks the work currently saved in the existing project. **Do not confuse checked software functionality with scientifically established image accuracy.** No final release has been packaged.

**Verified implementation checklist:** 73/126 items marked implemented (software tests where applicable); **pending:** 53. Existing software and scientific checklists are cumulative.
## Admin and customer interfaces
- [x] L001 — Separate HTML interface for customer site
- [x] L002 — Separate admin HTML/JS interface
- [x] L003 — Protect admin API with fail-closed token
- [x] L004 — Keep token out of local storage
- [x] L005 — Mobile-responsive admin layout
- [x] L006 — Food photo upload
- [x] L007 — Photo preview
- [x] L008 — Multi-food labels per plate
- [x] L009 — On-image bounding-box drawing
- [x] L010 — Session/batch grouping
- [x] L011 — Nutrition values per serving or 100g
- [x] L012 — Label source, recipe details and evidence
- [x] L013 — Optional plate diameter
- [x] L014 — Rights checkbox and server validation
- [x] L015 — Review approval/rejection panel
- [x] L016 — List pending examples
- [x] L017 — User correction review panel
- [x] L018 — Admin validation gate dashboard
- [ ] L019 — Role-based staff accounts
- [ ] L020 — Admin MFA and SSO
- [ ] L021 — Per-admin audit logs
- [ ] L022 — Password/token rotation administration
- [ ] L023 — Separate admin domain with hardened proxy
- [ ] L024 — User identity integration on deployed Reliv PWA

## Supervised data and nutrition correctness
- [x] L025 — Normalize nutrition to per-100g
- [x] L026 — Scale learned nutrition for 100g/300g user servings
- [x] L027 — Require edible portion in grams
- [x] L028 — Track weight as scale/packaging/estimate
- [x] L029 — Require explicit food type
- [x] L030 — Track recipe variant
- [x] L031 — Restrict numeric nutrient bounds
- [x] L032 — Record source notes/HTTPS link
- [x] L033 — Store original image only in private directory
- [x] L034 — Ensure matching is approval-gated
- [x] L035 — Prevent rejected labels becoming training data
- [x] L036 — Preserve mixed plate boxes
- [x] L037 — Group train/validation/test split by batch
- [x] L038 — Reject exact image leakage across different splits
- [x] L039 — Exclude unboxed mixed plates from classifier export
- [x] L040 — Exclude incomplete annotation groups from detector export
- [x] L041 — Export classification image crops
- [x] L042 — Export YOLO bounding boxes
- [x] L043 — Generate documented dataset manifest
- [x] L044 — Export image labels only for permission-attested photos
- [x] L045 — Generate scale-weighed 100g/300g pair manifests
- [ ] L046 — Third-party verification of all nutrient records
- [ ] L047 — Government Indian food table licensing/data integration
- [ ] L048 — Direct audited restaurant nutrition partnerships
- [ ] L049 — Recipe batch cooking-yield validation
- [ ] L050 — Laboratory analysis of representative meals
- [ ] L051 — Automatic data deduplication across near duplicates
- [ ] L052 — Nutrient confidence intervals from recipe variance

## Reference memory and learning loop
- [x] L053 — Normalize incoming JPEG/PNG/WEBP for comparison
- [x] L054 — Exact-photo matching to approved items
- [x] L055 — Conservative near-duplicate dHash candidate search
- [x] L056 — Never inherit grams from non-identical photos
- [x] L057 — Require user quantity confirmation
- [x] L058 — Separate user feedback consent
- [x] L059 — Optional photo consent for review
- [x] L060 — Store corrections as untrusted feedback
- [x] L061 — Review correction status without auto-training
- [x] L062 — Optional locally licensed CLIP-compatible semantic adapter
- [x] L063 — Image embedding indexing command
- [x] L064 — Human-reviewed learned item logging
- [ ] L065 — Calibrate semantic retrieval thresholds on held-out Indian food images
- [ ] L066 — Benchmark image similarity retrieval in diverse lighting
- [ ] L067 — Implement vector index for millions of examples
- [ ] L068 — Incremental embedding index invalidation on review
- [ ] L069 — Measure false food matches between visually similar recipes
- [ ] L070 — Automated versioned model training orchestrator
- [ ] L071 — Human-in-the-loop retraining with signoff
- [ ] L072 — Compare new model against prior model before promotion

## Testing and production engineering
- [x] L073 — API tests for locked admin endpoints
- [x] L074 — API tests for review state transitions
- [x] L075 — Exact-photo mixed-meal tests
- [x] L076 — Tests ensuring similar photos never inherit grams
- [x] L077 — Nutrient-basis normalization tests
- [x] L078 — Batch log tests
- [x] L079 — Image privacy/non-public URL test
- [x] L080 — Correction consent tests
- [x] L081 — Dataset export tests
- [x] L082 — Split leakage tests
- [x] L083 — Scale-only portion-pair tests
- [x] L084 — Admin validation dashboard no-fabrication tests
- [x] L085 — JavaScript syntax checks
- [x] L086 — Complete food-table arithmetic check
- [ ] L087 — Live iOS Safari device E2E
- [ ] L088 — Live Android Chrome camera E2E
- [ ] L089 — Full browser E2E without mocks in accessible environment
- [ ] L090 — Rate limits and request quotas
- [ ] L091 — Production API authentication for all profiles
- [ ] L092 — Image retention/deletion controls
- [ ] L093 — Encryption at rest and backups
- [ ] L094 — Load testing and latency SLOs
- [ ] L095 — Detailed error and telemetry capture
- [ ] L096 — Migration rollback and disaster recovery
- [ ] L097 — Malicious-image security review

## Real-world scientific acceptance
- [ ] L098 — Collect 500+ independent weighed real meals across cuisines
- [ ] L099 — Collect multi-camera/lighting/plate conditions
- [ ] L100 — Collect hundreds of 100g vs 300g pairs for rice/curry/pizza/pasta
- [ ] L101 — Train a new classifier with enough train samples per class
- [ ] L102 — Train a new multi-food detector using annotated objects
- [ ] L103 — Produce real-photo food recognition top-1 accuracy
- [ ] L104 — Produce independent detector mAP50 and mAP50:95
- [ ] L105 — Produce food weight mean/median/P90 absolute error
- [ ] L106 — Produce 100g vs 300g balanced-class sensitivity/specificity
- [ ] L107 — Produce measured kcal MAE and protein MAE
- [ ] L108 — Produce unknown-food rejection metrics
- [ ] L109 — Report class-wise precision/recall with uncertainty
- [ ] L110 — Benchmark restaurant/packaged SKU label accuracy
- [ ] L111 — Independent blinded comparison versus competitors
- [ ] L112 — Finish production security/privacy review
- [ ] L113 — Independent domain-expert nutrition validation
- [ ] L114 — Release gate signoff backed by actual evidence

**External camera model accuracy:** not measured. **Food-detection mAP:** not measured. **Automatic edible-mass MAE:** not measured. **Production release:** not approved.

Operational guide: [ADMIN_LEARNING_GUIDE.md](ADMIN_LEARNING_GUIDE.md). Existing broader roadmap: [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md).

## October 29 correction-workflow additions (in the same master project)
- [x] L115 — Admin view of approved food references
- [x] L116 — Admin revocation of bad approved nutrition labels with recorded reason
- [x] L117 — Revoked references stop matching and leave future training exports
- [x] L118 — Historical customer food logs survive reference revocation
- [x] L119 — Private photo preview for authenticated administrators
- [x] L120 — Separate user consent for photo review versus training/reference use
- [x] L121 — Correction prefill retains food and weight but requires admin verification of nutrition
- [x] L122 — Independent existing customer scan, text, restaurant, barcode and diary paths remain functional
- [ ] L123 — Authenticated multi-role production admin accounts and audit signatures
- [ ] L124 — Approved-correction feedback loop triggers validated retraining/redeployment
- [ ] L125 — Verified production integration and real-device iOS/Android QA
- [ ] L126 — Blind Indian mixed-food image accuracy, detection mAP and portion weight benchmarking
