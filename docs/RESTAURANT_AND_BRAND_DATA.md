# Restaurant and branded food nutrient sourcing

## Verified menu ≠ verified calories

Official Arsalan menu: https://arsalanrestaurants.com/menu/

Official Biryani By Kilo item page: https://biryanibykilo.com/item-1590/22-chicken-hyderabadi-dum-biryani

These establish specific menu names, variants and advertised package sizes. The pages inspected did not establish an exact protein/calorie profile per edible serving. They must not be combined with a generic recipe value and then labeled **“Arsalan nutritional facts”**. For BBK products, advertised 0.5kg and 1kg pack sizes are not per-person consumption, and bones/packaging/condiments can change edible mass.

Kareem's: a suitable official menu and nutrition fact source for the requested specific business was not established during this audit. Do not fabricate its menu and nutrition.

### Source hierarchy

1. An official manufacturer/restaurant nutrition label matching a specific SKU/menu variant and serving measure, reviewed and documented.
2. USDA FoodData Central Foundation/SR Legacy/FNDDS record for the **correct cooking state** (public domain, per-100g); cannot be automatically substituted for restaurant meals.
3. Recipe nutrition computed from weighed ingredients + measured cooked yield and oil/ghee, with tracked ingredient provenance.
4. Open Food Facts product nutrition for the **correct barcode** with community-data verification warning. Terms: https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/
5. An unverified generic recipe / visual portion guess, explicitly marked as approximate.
6. If insufficient information, show **Unknown; please confirm**, rather than a made-up calorie number.

### Operational import

`RELIV_RESTAURANT_NUTRITION_CSV` accepts an *operator-reviewed* CSV with columns:

`brand,dish,kcal_100g,protein_100g,carbs_100g,fat_100g,evidence_url,verified_on,reviewer`

**The input is not automatically third-party verified.** A named reviewer and source URL are operator attestations only; validate the document, serving basis, cooking state, date and legal reuse rights yourself. Do not promote data without review.

The search endpoint `/api/restaurants?q=Arsalan` lists known official-menu variants. `/api/restaurants/estimate` returns no nutrition by default if authoritative restaurant data are absent. `use_generic_estimate=true` explicitly computes an approximate generic value; `/api/restaurants/log` retains that source in history. A pure-restaurant label is never silently substituted.

### Packaged drinks

`/api/products/search?q=Epigamia` and `/api/products/barcode/{barcode}` require live Open Food Facts access. Select the exact Coca-Cola or Epigamia barcode and volume; no claim of a universal “Epigamia protein shake” profile is made. Compare the photographed nutrition label to the returned fields; variants and formulations change. OFF is rate-limited (10 search requests/min/IP, 15 product reads/min/IP at documentation time), so do not implement uncontrolled search-as-you-type.
