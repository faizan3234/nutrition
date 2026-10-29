from playwright.sync_api import sync_playwright
from pathlib import Path
import json
root=Path(__file__).resolve().parent.parent/'web'
html=(root/'index.html').read_text().replace('<link rel="manifest" href="/assets/manifest.webmanifest">','').replace('<link rel="stylesheet" href="/assets/style.css">','').replace('<script src="/assets/app.js" defer></script>','')
style=(root/'style.css').read_text()
script=(root/'app.js').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,view in [('desktop',{'width':1366,'height':900}),('mobile',{'width':390,'height':844})]:
  page=b.new_page(viewport=view)
  errors=[]
  page.on('pageerror',lambda err: errors.append(str(err)))
  page.set_content('<style>'+style+'</style>'+html)
  page.evaluate('''() => {
     Object.defineProperty(window, 'localStorage', {value:{
       getItem:(key)=>null,setItem:(key,value)=>{},removeItem:()=>{}},configurable:true});
     Object.defineProperty(window, 'crypto', {value:{randomUUID:()=> 'uuid-1'},configurable:true});
     window.fetch = async (url,opt) => {
       let payload;
       if(url.startsWith('/api/foods')) payload={items:[{id:'masala-dosa',name:'Masala Dosa',category:'South Indian',kcal:215,protein:5,carbs:30,fat:8,default_grams:180,aliases:[],source:'illustrative_starter_not_verified'}]};
       else if(url.startsWith('/api/me/plate')) payload={plate:null};
       else if(url.startsWith('/api/me/shortcuts/') && url.endsWith('/log')) payload={grams:90,protein:4.5,kcal:100};
       else if(url.startsWith('/api/me/shortcuts') && opt?.method==='POST') payload={id:'shortcutA'};
       else if(url.startsWith('/api/me/shortcuts')) payload={items:[{id:'shortcutA',nickname:'Usual dosa',food_name:'Masala Dosa',serving_amount:180,unit:'g'}]};
       else if(url.startsWith('/api/products/label/log')) payload={id:'label-logA',protein:18,kcal:150};
       else if(url.startsWith('/api/model-info')) payload={ready:false,provider:'none'};
       else if(url.startsWith('/api/day')) payload={items:[],totals:{kcal:0,protein:0,carbs:0,fat:0}};
       else if(url.startsWith('/api/products/search')) payload={items:[]};
       else if(url.startsWith('/api/restaurants')) payload={items:[{brand:'Arsalan',dish:'Chicken Biryani',menu_url:'https://arsalanrestaurants.com/menu/',verified_menu_item:true,nutrition_verified_for_specific_dish:false,advertised_pack_weight_g:null}]};
       else if(url.startsWith('/api/parse-meal')) payload={items:[{kind:'generic_food',food:{id:'masala-dosa',name:'Masala Dosa',category:'South Indian',kcal:215,protein:5,carbs:30,fat:8,default_grams:180,aliases:[],source:'illustrative'},grams:100,unit:'g'}]};
       else if(url.startsWith('/api/reference-foods')) payload={items:[{fdc_id:123,name:'Rice, white, cooked',category:'Foundation',per_100g:{kcal:130,protein:2.7,carbs:28,fat:0.3},source_url:'https://fdc.nal.usda.gov/food-details/123/nutrients'}]};
       else payload={message:'stub response'};
       return {ok:true,status:200,json:async()=>payload};
     };
   }''')
  page.add_script_tag(content=script)
  page.wait_for_timeout(300)
  print(name,'errors',errors,'tiles',page.locator('.food-tile').count())
  page.locator('#heroScan').click()
  assert page.locator('#tab-scan').is_visible()
  page.locator('.food-tile').first.click()
  assert page.locator('.result').count()==1
  page.locator('[data-usual]').first.click()
  page.locator('#usualDetails summary').click()
  page.wait_for_timeout(80)
  assert page.locator('[data-usual-log]').count()==1
  page.locator('[data-usual-factor]').select_option('0.5')
  page.locator('[data-usual-log]').click()
  page.locator('#plateDiameter').select_option('26')
  page.locator('#savePlate').click()
  page.locator('#moreWays summary').first.click()
  page.locator('summary').filter(has_text="Can't find your package?").click()
  page.locator('#manualBrand').fill('Example')
  page.locator('#manualProduct').fill('Protein drink')
  for n in ['manualKcal','manualProtein','manualCarbs','manualFat']:page.locator('#'+n).fill('20')
  page.locator('#manualAmount').fill('300')
  page.locator('#confirmLabel').check()
  page.locator('#logManualLabel').click()
  page.wait_for_timeout(80)
  assert not errors,errors
  page.locator('#productSearch').fill('Epigamia')
  page.locator('#searchProductBtn').click()
  print(name,'result',page.locator('.result').count(),'productUI',page.locator('#barcodeInput').count(),'JS errs',errors)
  page.locator('#restaurantSearch').fill('Arsalan')
  page.locator('#restaurantSearchBtn').click()
  page.wait_for_timeout(100)
  assert page.locator('#restaurantResults .product-item').count()==1
  page.locator('#mealText').fill('100g masala dosa')
  page.locator('#parseTextBtn').click()
  page.wait_for_timeout(100)
  assert page.locator('#textResults .product-item').count()==1
  page.locator('#referenceSearch').fill('rice')
  page.locator('#referenceSearchBtn').click()
  page.wait_for_timeout(100)
  assert page.locator('#referenceResults .product-item').count()==1
  assert not errors,errors
  print(name,'restaurant/text/reference UI rendered; no JS errors')
  page.screenshot(path=f'/mnt/data/reliv_nutrition_{name}.png',full_page=True)
  page.close()
 b.close()
