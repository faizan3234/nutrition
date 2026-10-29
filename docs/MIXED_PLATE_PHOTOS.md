# Mixed plates, drinks and leftovers

This change adds user-selected food-region analysis to the customer Scan screen. It does not supply trained weights or establish recognition/portion accuracy.

1. Upload a photo. For screenshots, select only the food area, excluding surrounding personal details.
2. Drag rectangles around separate foods, or use the keyboard-accessible percentage coordinates. Up to six regions can be selected. Undo/Clear correct selections.
3. Analyse. The configured existing model sees each crop separately. Plate size and the second image are intentionally not passed to cropped inference: their coordinate systems no longer match. Use whole-image analysis to retain those inputs.
4. Review candidates. Ambiguous names no longer silently select a recipe by shared words. Choose a suggested catalogue dish or search manually. Unknown food remains unresolved.
5. Enter each food's edible amount and consumed fraction, then explicitly confirm each photo result before individual/batch logging. Typical starting servings are not measured weights. Nutrients remain only as reliable as the selected recipe/data source.

## Examples motivating the workflow

- Rice covered by several curries: select distinguishable components, but expect occlusion and overlapping gravy to require manual correction. Never assume visible surface area is the portion mass.
- Corn chaat: select a matching recipe; plain boiled corn alone omits additions.
- Biryani or seasoned rice: confirm meat/vegetable variant, added fat and edible mass excluding bones. Do not count a full biryani recipe and its meat/rice again.
- Pasta and garlic bread: select separate regions for pasta and bread. Cheese/sauce normally belongs in the pasta recipe; add extras only if not included.
- Mocktails: confirm recipe/syrup and liquid ml excluding ice. Colour cannot establish sugar content.
- Chaat and covered desserts: hidden fillings/toppings require recipe or label information.
- Breakfast platter: select separate foods; confirm sausage type and sandwich filling.
- Smaller/larger rice portions or leftovers: separate quantities must come from user confirmation or scales. Two photos are not automatically a before/after subtraction. Log the consumed amount, not both plates.

## API

`POST /api/analyze` retains existing fields and adds optional `regions`:

```json
{"image_base64":"<real base64 image>","regions":[{"x1":0,"y1":0,"x2":0.5,"y2":1}]}
```

Coordinates are normalized 0–1 after EXIF orientation, minimum width/height .02. At most six regions. Results include region numbers and normalized source-image boxes. Crop results discard provider/reference mass; quantity must be entered. Per-region missing models/RuntimeError failures remain visible. Whole-image YOLO results retain detector boxes. ONNX runner-up classes are alternatives, not additional foods. Region mode is user-assisted cropping, not automatic segmentation, and does not guarantee identifying all foods within a crop.

## Validation and remaining work

Regression tests cover crop pixels/coordinates, bounded requests, ambiguous matches, classifier alternatives and partial failures. Tests use controlled model responses, not accuracy ground truth. Uploaded example JPEGs were decoded locally; none were committed or submitted to an external model. Food names, weights, recipe data and permission for reuse are not inferred as training labels.

For measurable improvement, collect authorized scale-weighed recipes and region annotations, train licensed detector weights, and evaluate on independent kitchens/sessions. Measure class accuracy, detector mAP, mass MAE and nutrient errors separately. Exact nutrients cannot be promised from a photograph alone. Source-verified nutrient records and confirmed edible quantities remain essential.

## Quantity provenance and leftovers follow-up

Photo/classifier confidence is not measured nutrition accuracy. ONNX softmax values are now shown conservatively: top score below 0.5 or a top-two margin below 0.15 requires choosing a candidate instead of automatically selecting a dish. These thresholds are uncalibrated review heuristics, not validated confidence intervals; confident wrong predictions remain possible. No new recognition percentage is claimed.

Each ordinary or batch meal log can include `quantity_basis`, `unit`, and `leftover_amount`. Existing clients remain supported and receive `unspecified` provenance. Example:

```json
{"profile":"example-user","food_id":"steamed-rice","grams":300,"leftover_amount":125,"quantity_basis":"scale","unit":"g","meal":"Lunch"}
```

This records 175 g consumed. A leftover amount and a non-100 consumed percentage cannot both be supplied. Leftovers must be nonnegative and smaller than served; remove an item if none was eaten. Both amounts must use the same edible-food basis, excluding containers and bones. Choosing `scale` or `measuring_container` records the user's statement, not independent sensor verification. Percent-eaten values can still be estimated even when the original serving was weighed.

The source selection and leftover amount persist in SQLite and survive diary reloads. Old logs migrate without changing their nutrition totals. Diary entries display quantity provenance and nutrient source separately. A weighed portion using the illustrative catalogue remains an illustrative calorie/protein estimate.

Explicit unit mismatches are rejected. `scale` cannot imply ml and `measuring_container` cannot imply grams; density conversion is not implemented. Photo-provider mass guesses for drinks are also discarded rather than relabelled as ml; a typical starting volume remains explicitly unmeasured. Unit remains optional for backward-compatible clients. Per-food quantities in a mixed plate remain independent. The batch endpoint validates all items before storing any.

Nonfinite imported nutrient values are rejected. NaN protein must never enter a food record and silently corrupt daily totals.

### Evidence for the follow-up

API regression tests cover served-minus-leftover calculations, mixed-plate protein/calorie totals, persistence, old database migration, unit mismatches, atomic batch failure, uncertain classifier review and invalid imported values. `scripts/test_portion_ui.cjs` exercises real customer JavaScript in jsdom with mocked HTTP: leftovers, totals, confirmation reset, invalid inputs, liquid units and single/batch payloads. It is not a visual browser or mobile-camera test. CI installs pinned jsdom for this check.

No weighed real-photo benchmark, calibrated portion model or verified nutrition dataset was created in this change. Recognition, mass and nutrient error metrics remain unmeasured. Before claiming reliable automatic tracking, run licensed model weights against an independent set with verified dish identities, edible scale weights, ingredient nutrition and cooked yields; report per-food errors and unknown-food failures, not just aggregate software pass counts.
