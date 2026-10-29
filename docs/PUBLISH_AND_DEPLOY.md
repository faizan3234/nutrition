# Publishing the final project to GitHub / Reliv PWA

**This source is NOT already uploaded to GitHub or deployed.** The Git bundle contains the complete local Git history; the ZIP contains the latest source without `.git` internals.

## Create the intended new repository

1. On GitHub, create a new **private** repository named `reliv-nutrition-ai` under the desired account. Do **not** initialize it with a README or `.gitignore` (those already exist in this project).
2. From the extracted final source ZIP:
   ```sh
   git init -b main
   git add .
   git commit -m "Reliv Nutrition AI consolidated source handoff"
   git remote add origin https://github.com/YOUR_ACCOUNT/reliv-nutrition-ai.git
   git push -u origin main
   ```
   Alternatively, clone the separate final **Git bundle** to retain previous commits, then add `origin` and push:
   ```sh
   git clone Reliv_Nutrition_AI_FINAL_2026-10-29.bundle reliv-nutrition-ai
   cd reliv-nutrition-ai
   git remote add origin https://github.com/YOUR_ACCOUNT/reliv-nutrition-ai.git
   git push -u origin main
   ```
3. Keep the repository private initially. Never commit `.env`, personal photos, customer SQLite files, provider keys, model/data assets without license permission, or personal nutrition history.

## Deployment architecture

- Customer website `/` and admin panel `/admin` are served from **one backend**. They may be split into customer/admin *domains* at your reverse proxy, but admin endpoints must remain protected.
- Host `app.main:app` behind HTTPS and a production-grade reverse proxy; the compose template is bound to localhost intentionally.
- Before public access, integrate the Reliv user identity service and secure session mechanism. `RELIV_ENV=local` is an unsecured demo mode.
- Use a persistent encrypted volume for database and private admin/upload photos; set backups, deletion/retention controls and abuse limits.
- Keep provider, USDA and admin keys in a secure server-side secrets manager.
- Run `python -m pytest -q`, arithmetic checks, independent real-photo benchmarks, on-device accessibility/device testing and security assessment before promoting a release.

## PWA integration

Use `examples/relivpwa_integration.js` and `docs/DEPLOY_INTEGRATE.md` as a starting integration contract. Make the nutrition API same-origin or configure strict `CORS_ALLOWED_ORIGINS`. Use authenticated user IDs (and corresponding production JWTs), **not** anonymous demo profile strings.

This project must not replace, overwrite or silently deploy to the existing Reliv PWA repository. First stage the integration in a separate branch and verify account/session boundaries.
