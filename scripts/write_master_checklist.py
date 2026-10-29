"""Evidence-based roadmap; never mark model accuracy verified without real held-out predictions."""
from collections import Counter
from pathlib import Path

# Each phase contains completed engineering checks and external/research blockers.
PHASES={
'01 · Repository & architecture':{
 'done':['Modular FastAPI application','Independent food catalogue module','Vision model adapter abstraction','Nutrition calculation module','SQLite persistence module','Local mobile website','PWA install manifest','Offline static asset service worker','Docker container recipe','Docker Compose local persistence','GitHub Actions automated test workflow','Dependencies separated for core/vision'],
 'open':['Create brand-new remote GitHub repository','Publish verified tagged production release','Set up staged deployment environments']},
'02 · Indian and international food coverage':{
 'done':['North Indian food examples','South Indian food examples','Bengali/East Indian examples','West Indian examples','Rice and biryani examples','Pizza examples','Pasta examples','Noodle and Asian examples','Fast food and snacks examples','Sausage and egg examples','Fruit and nuts examples','Drinks and generic shake examples','Aliases for many spelling variants','Complete searchable food CSV export'],
 'open':['Validate every recipe against licensed reference data','Independently test each catalogue food in camera photos','Integrate multilingual Hindi food name synonyms','Integrate multilingual Bengali food name synonyms','Create region-specific recipe variants','Measure out-of-distribution unknown-food rejection']},
'03 · Packaged food / beverage lookup':{
 'done':['Open Food Facts integration module','Barcode format validation','Per-100 nutrition label normalization','Volume-versus-mass unit selection','Reject incomplete nutrition labels','Prevent NaN/negative nutrient values','Packaged product search endpoint','Packaged product barcode endpoint','Packaged product logging endpoint','Product source attribution in API','Mocked cola 100ml versus 300ml arithmetic test','Mocked branded protein-shake 100ml versus 300ml test','Client-side branded product search UI','Client-side barcode-entry UI','Optional browser barcode-camera workflow'],
 'open':['Validate real Open Food Facts network integration','Verify Coca-Cola regional SKUs against photographed labels','Verify Epigamia variant labels against actual packaging','Implement product-specific serving size suggestions','Implement package nutrition label OCR and user correction','Set API rate limits/caching policy with provider','Create verified Indian branded-products QA sample']},
'04 · Photograph capture':{
 'done':['Phone photo file input','JPEG/PNG/WEBP validation','EXIF orientation handling','Large image dimension limit','Upload byte-size limit','Optional second-camera-angle input','Known plate diameter entry','Second photo included in vision request','Photo preview in website','Explicit user-triggered photo upload'],
 'open':['Actual Android Chrome camera test','Actual iOS Safari camera test','Unsupported camera/device fallback QA','Low-light and glare image QA','Photo retention policy and deletion compliance','Accessibility review of capture experience']},
'05 · Food recognition':{
 'done':['Local YOLO detector adapter','Operator-supplied NutriLens 22-label adapter','Configurable CLIP adapter','No fabricated closed-set weight output','Unmatched dish flagged for correction','Camera provider readiness API','Recognized food matched conservatively','Groq online packaged food search integration'],
 'open':['Acquire legally usable food detector model weights','Acquire legally usable Indian food classifier weights','Train on a licensed Indian food image dataset','Train on mixed Indian thali images','Benchmark top-1 classification accuracy','Benchmark top-5 classification accuracy','Evaluate per-class confusion and unknown food','Benchmark performance on global foods','Measure real mixed-plate mAP@0.50','Measure real mixed-plate mAP@0.50:0.95','Cross-test unseen phones and locations','Choose best model using held-out evidence']},
'06 · Portion and food mass':{
 'done':['User-entered grams supported','Optional plate-size parameter in AI prompt','Optional second view in AI prompt','Report AI weight as estimate not scale measurement','Return uncertainty ranges if inferred','Fallback default serving explicitly labeled','Never return a measured-mass flag for a photograph'],
 'open':['Train mass regressor with measured gram labels','Use Nutrition5k held-out mass ground truth','Create Indian weighed meal benchmark','Physical plate calibration validation','Measure 100g versus 300g classification performance','Test overlapped items separately','Test liquid volume in transparent containers','Test thick curry under opaque sauce','Test bowl depth and occlusion','Quantify gram MAE and error intervals','Determine worst-case underestimation rate','Benchmark against digital kitchen scale readings','Test 10 kitchen lighting conditions']},
'07 · Nutrition provenance and formulas':{
 'done':['Decimal half-up per-100 serving arithmetic','Calories formula scales with amount','Protein formula scales with amount','Carbohydrate formula scales with amount','Fat formula scales with amount','Precision and rounding regression tests','Food source field in API','Optional source-attributed replacement CSV','Validate imported CSV numeric ranges'],
 'open':['License and import IFCT values','License and import INDB recipe values','Use USDA FDC CC0 for non-Indian reference items','Version each source dataset','Trace macros to recipes/ingredients','Validate recipe oil and ghee variation','Validate cooked versus raw weight basis','Validate food density across recipe variations','Test calorie versus label values','Test protein versus laboratory/reference labels','Measure calibration of uncertainty estimates']},
'08 · Meal diary and dashboard':{
 'done':['Save manual food log','Save packaged food log','Save 2–12 mixed-plate components atomically','Read daily diary','Remove food log','Calculate daily calories','Calculate daily protein','Calculate daily carbohydrates','Calculate daily fat','Show editable portion fields','Set daily calorie goal','Set daily protein goal','Group foods by breakfast/lunch/dinner/snacks','Store source and quantity unit'],
 'open':['Add verified account authentication','Sync food history with existing Reliv user accounts','User-controlled photo deletion','Export diary as JSON or CSV','Handle travel between timezones accurately','Dietitian-reviewed goal guidance']},
'09 · Browser and device quality':{
 'done':['Frontend JavaScript syntax check','Browser DOM smoke test using mocked API responses','Client HTML input constraints','Mobile layout CSS','Food search result DOM rendering','Branded search result DOM rendering','Barcode fallback manual entry','Status display for unavailable camera provider','Disable unfinished product labels from logging'],
 'open':['End-to-end browser automation on served URL','Android real-device smoke test','iPhone real-device smoke test','Screen reader usability check','Voice input and speech feedback','Test offline-to-online reconnection','Performance test on low-end Android phones','Accessibility WCAG audit']},
'10 · Unit and integration tests':{
 'done':['FastAPI health test','Food coverage test','100g versus 300g nutrient test','Invalid serving input test','Mixed plate batch logging test','Batch atomicity test','Batch size constraint test','Branded product normalization test','Branded product incomplete-nutrients test','Barcode input validation test','Packaged food logging integration test','Packaged search mock test','No-vision provider explicit status test','Two-photo API payload test','Fake unmatched food not given nutrients','IoU geometry unit test','mAP perfect-prediction fixture test','mAP wrong-class fixture test','mAP false-positive fixture test','Group-wise train/validation/test split leak test','Deterministic split test','Full nutrition-arithmetic catalogue check'],
 'open':['Live local YOLO weights inference test','Live NutriLens H5 inference test','Live Groq online packaged search test','Live Open Food Facts integration test','Camera pipeline performance load test','API access-control penetration tests','Automated UI screenshot acceptance test']},
'11 · Benchmark design':{
 'done':['Separate classification and nutrient accuracy metrics','Photo benchmark runner','Mixed-plate mAP metric runner','Calories MAE metric runner','Protein MAE metric runner','Gram MAE metric runner','Train/validation/test split manifest tool','No fabricated model scores','No copied upstream accuracy claims'],
 'open':['Download licensed Indian image training images','Download Nutrition5k mass-labeled photos','Run Indian dish holdout inference','Run mixed thali holdout inference','Run model mass regression inference','Run calories/protein ground truth evaluation','Calculate 95% confidence intervals','Test worst-case tail error','Run independent unseen-device validation','Publish model card and per-class results','External replication of accuracy report']},
'12 · Training and optimization':{
 'done':['Classifier transfer-learning script','Multi-food detector training script','Fixed random seed options','Early stopping and validation checkpoint'],
 'open':['Run GPU classifier training','Run GPU detection training','Improve poor minority-food classes','Perform class-balanced augmentation','Run food-specific segmentation training','Train ingredient composition estimator','Train portion/mass estimator','Tune confidence thresholds on validation set','Temperature-scale model confidence','Benchmark ensemble versus best single model','Quantize model after accuracy checks','Benchmark edge-device latency','Measure cost per 1,000 scans','Document reproducible hardware and training duration']},
'13 · Security, privacy, and compliance':{
 'done':['Server-side private AI key only','No camera upload until user action','Reject malformed base64 images','Limit image pixels and bytes','Protect API errors from echoing secrets','Use parameterized SQLite queries','Use exact barcode format validation','Block incomplete community product labels'],
 'open':['Real login / authorization for diary records','Production rate limiting','TLS and secure origin end-to-end','Camera/photo privacy notice and consent','Photo deletion and retention jobs','Terms and privacy policy review','Threat model for user-uploaded photos','AI prompt-injection regression testing','Account deletion request implementation','Healthcare compliance/legal review','Third-party image model license review','Third-party dataset use rights review','Open Food Facts attribution and ODbL audit']},
'14 · Deployment and release':{
 'done':['Docker configuration','Environment example','Local database persistence option','PWA client SDK example','API documentation via FastAPI OpenAPI','Source repo commits prepared','Food catalogue exported for download'],
 'open':['Configure deployed vision key or licensed weights','Run live smoke tests on hosted site','Connect secure Reliv authentication','Attach PWA Nutrition tab in existing repository','Set database backups','Set error tracking and budget alarms','Enable production metrics','Create new GitHub remote repository','Push source to newly created remote repository','Deploy staging instance','Deploy production instance','Rotate production API credentials']},
'15 · Market-leading accuracy claims':{
 'done':['No unsupported market-superiority claim','Accuracy report distinguishes tests from camera benchmarks'],
 'open':['Benchmark against at least 3 competing systems','Obtain written repeatable evaluation protocol','Demonstrate superiority on Indian dishes','Demonstrate superiority on mixed plates','Demonstrate superiority for 100g versus 300g','Demonstrate superiority for branded food lookup','Independent study with confidence intervals','Publish methods and calibration plots','Obtain reviewer/dietitian validation','Legal marketing claim review']},
}

def main():
    root=Path(__file__).resolve().parent.parent
    docs=root/'docs';docs.mkdir(exist_ok=True)
    completed=sum(len(v['done']) for v in PHASES.values())
    open_count=sum(len(v['open']) for v in PHASES.values())
    lines=['# Reliv Nutrition AI — Evidence-based master checklist','','**Status: '+str(completed)+' verified implementation checks; '+str(open_count)+' pending items; '+str(completed+open_count)+' total**.','',
    'Checked means the relevant implementation exists and passed software-level checks when applicable.',
    'It does NOT mean independently measured camera accuracy, commercial readiness, or clinical validation.',
    'No external dataset or trained model may be marked completed without saved evidence.',
    '', '## Highest-priority blockers','',
    '1. Acquire lawful image datasets and pre-trained weights; execute GPU training and inference.',
    '2. Weigh real Indian mixed meals and evaluate photo-predicted grams, calories, protein and mAP.',
    '3. Replace illustrative food nutritional values with verified licensed food composition data.',
    '4. Authenticate users; enforce security, consent, retention and product data licensing.',
    '5. Test deployed site on actual Android/iPhone cameras, then compare against competitors.',
    '']
    for title,parts in PHASES.items():
        lines += [f'## {title}', '']
        lines += [f'- [x] {task}' for task in parts['done']]
        lines += [f'- [ ] {task}' for task in parts['open']]
        lines.append('')
    lines += ['## Test evidence','',
              '- `python -m pytest -q` — API, math, product-label, batch, metadata and evaluation-tool tests.',
              '- `python -m scripts.audit_calculations` — current catalogue × ten masses × four macros.',
              '- `node --check web/app.js` — static JS parser check.',
              '- `python -m scripts.evaluate_detection --ground-truth ... --predictions ...` — real mAP, requires actual annotations and predictions.',
              '- `python -m scripts.evaluate_photos ...` — real single-food photo tests, requires operator-supplied model and labeled photos.',
              '- `python -m scripts.evaluate ...` — gram/kcal/protein MAE, requires independent weighed meals.',
              '- Synthetic unit-test fixtures are not a genuine model benchmark.',
              '', '### Unsupported marketing statements','',
              'Do not claim **most accurate**, **highest mAP**, **exact food weight from one photograph**, **lab-verified nutrients**, **all foods automatically recognized**, or **best in the market** without an independent market comparison and measured validation.']
    (docs/'MASTER_CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    import json
    (docs/'checklist_status.json').write_text(json.dumps({'completed':completed,'pending':open_count,'total':completed+open_count,
       'scope':'engineering checklist not camera accuracy',
       'sections':[{ 'name':n,'completed':len(v['done']),'pending':len(v['open'])} for n,v in PHASES.items()]},indent=2)+'\n',encoding='utf-8')
    print(completed,open_count,completed+open_count)

if __name__=='__main__':main()
