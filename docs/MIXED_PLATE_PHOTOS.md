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
