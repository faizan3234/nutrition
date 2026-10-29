# Reliv Nutrition AI — v0.4 release report (29 Oct 2026)

## What was actually tested

- **37/37 unit and API tests passed** (not a production penetration test).
- **7720/7720 arithmetic checks passed**, across 193 illustrative food entries × 10 portion quantities × four nutrients.
- `node --check web/app.js` passed; Python code can be compiled.
- Mocked Open Food Facts cases confirmed nutrition normalization, rejection of incomplete product labels, exact variant selection and scaled beverage amounts (100ml/300ml).
- Atomic mixed-plate logging and mathematical mAP evaluator tests passed.
- A local Chromium DOM smoke run with stubbed API data succeeded on 1366px desktop and 390px mobile widths with no JavaScript page errors; it verified UI rendering, a searchable food result and packaged-product input. **Real device camera behavior and live API networking remain untested.** The environment blocked navigation to the locally served app (`ERR_BLOCKED_BY_ADMINISTRATOR`).

## What has NOT been established

| Measure | Current result |
|---|---|
| Top-1 accuracy of Reliv camera model | **Unknown: 0 independently tested images** |
| Real mixed-plate detection mAP50 / mAP50–95 | **Unknown: 0 evaluated model predictions** |
| 100g vs 300g correctly predicted from photo | **Unknown: no weighed-photo test** |
| Gram MAE from camera | **Unknown** |
| Calorie/protein MAE from camera | **Unknown** |
| Validation of all food composition values | **Incomplete; current table illustrative** |
| Live Open Food Facts API communication | **Not tested in this restricted environment** |
| Live paid cloud vision API | **Not tested; no private API key configured** |
| Real-device barcode scanner | **Not tested** |
| Independent competitor comparison | **Not performed** |

**There is no defensible overall Reliv Nutrition AI camera accuracy percentage for this release.** 100% arithmetic checks means only that multiplication is implemented correctly. It does not imply nutrition truth or food identification accuracy.

## Food coverage

- **193 search/loggable generic foods**; group examples include North/South/East/West Indian food, pizza, pasta, burgers, sausages, rice, dal, drinks, snacks and protein dishes.
- Open-ended **branded product lookup** by name and exact barcode, conditional on actual Open Food Facts coverage and an Internet-connected server.
- Closed-set original NutriLens optional adapter: **22 visual categories only**. Gemini open-vocabulary and YOLO adapters are optional and unbenchmarked here.
- User quantity input, multi-item manual confirmation and corrections are supported; precise automatic mass is unproven.

## Source code integration

- Run `uvicorn app.main:app --host 0.0.0.0 --port 8000` after dependencies; see `README.md`.
- Deploy behind HTTPS with `VISION_PROVIDER=gemini` + protected server-side `GEMINI_API_KEY`, or install permitted open weights for another adapter.
- For existing Reliv PWA use `examples/relivpwa_integration.js`. Implement real user authentication and server authorization before any live user deployment.
- Third-party models, datasets, keys and licensed nutrition data are **not** included.

## Checklist

See [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md): 150 implemented checks, 139 pending tasks, 289 total. Checked engineering tasks are **not** scientific validation.
