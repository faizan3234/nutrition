# Deploy and connect to Reliv PWA

## Local setup

```sh
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest httpx
cp .env.example .env            # Windows: copy .env.example .env
# Set VISION_PROVIDER=gemini and GEMINI_API_KEY=<your secret> for photo analysis
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The JSON API is at <http://127.0.0.1:8000/docs>.

**Camera input in remote mobile browsers requires HTTPS** (localhost is a special case). Host behind a TLS reverse proxy or managed HTTPS server; protect keys on the server, never in JavaScript. Do not rely on Flask/SQLite unauthenticated profile IDs for private production health information.

## Docker

```sh
docker compose up --build -d
```

The named volume persists logged meals; `.env` is ignored by Git. Review data retention, consent, authentication, rate limits and CORS before exposing to the public internet. API does **not** implement production user authentication. The demo profile mechanism is insufficient for multi-user sensitive data.

## Activate camera model

`VISION_PROVIDER=auto` uses Gemini only if `GEMINI_API_KEY` is present. To explicitly select it, use `VISION_PROVIDER=gemini`. `GEMINI_MODEL` defaults to `gemini-2.5-flash` but providers may change model availability. Verify your available model ID and image-input quota.

For optional locally hosted models, see [MODEL_SETUP.md](MODEL_SETUP.md). If AI is not configured the UI still supports search and manual tracking.

## Reliv PWA

See [`examples/relivpwa_integration.js`](../examples/relivpwa_integration.js). Prefer a same-origin reverse proxy of `/nutrition-api` to the backend and tie meal logs to a real authenticated user ID. If served cross-origin, set `CORS_ALLOWED_ORIGINS=https://your-pwa-domain` and an API authentication solution.

### API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/model-info` | Actual configured provider and unmeasured accuracy flags |
| `GET /api/coverage` | Total catalogue count, categories, NutriLens label list |
| `GET /api/foods?q=dosa` | Search all manually loggable foods |
| `POST /api/analyze` | 1 or 2 base64 photo data URLs + optional plate diameter |
| `POST /api/log` | Log a **confirmed** food ID, grams and meal period |
| `GET /api/day` | List and summarize logged meals |
| `DELETE /api/log/{id}` | Delete a logged meal from demo profile |

### `/api/analyze` example

```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "secondary_image_base64": null,
  "plate_diameter_cm": 26
}
```

For a returned food `food.id` and **user-confirmed** `grams`, call `POST /api/log` with `{ "profile": "some-long-demo-id", "food_id": "masala-dosa", "grams": 300, "meal": "Breakfast" }`. The demo profile ID should be replaced with authenticated user identity for real users.

## Customer coach integration (31 October 2026)

The customer PWA calls this API using `VITE_NUTRITION_API_URL`. Set `CORS_ALLOWED_ORIGINS` to the actual HTTPS PWA origin. Keep this API in the nutrition repository; deploy independently from the customer UI and the offline kiosk backend.

`/api/coach` is disabled by default. Enable only on a protected deployment with `COACH_ENABLED=true`, server-only `GROQ_API_KEY` and an available `GROQ_COACH_MODEL`. Production requires a `profile_id` and matching short-lived Authorization Bearer token issued by the trusted auth service. The guest customer PWA does not yet have this auth bridge, so public conversational replies remain blocked until it is supplied. Add distributed rate limits and provider spending limits before public rollout. Replies contain text and an empty actions list: model output never directly changes records or payments.

The Vercel entrypoint now defaults to production access checks. `/tmp` SQLite is temporary serverless storage, not durable cloud history; provision durable storage before enabling multi-device record sync. Food-photo recognition still needs configured model assets/provider and real-device validation. The starter food catalogue is illustrative, not independently validated nutritional composition.
