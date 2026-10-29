/* Reliv Nutrition AI. Vanilla JS, no build tooling. Content is unverified demo nutrition. */
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const today=()=>new Date().toLocaleDateString('en-CA');
const externalSession=window.RELIV_NUTRITION_SESSION||null; // host app injects {profile,token} after verified login
const profile=externalSession?.profile || localStorage.getItem('reliv_profile') || (crypto.randomUUID?.() || Math.random().toString(36).slice(2));
localStorage.setItem('reliv_profile',profile);
let goals=JSON.parse(localStorage.getItem('reliv_goals')||'{"kcal":2000,"protein":90}');
let chosenFile=null,sideFile=null,results=[],foods=[],currentDay={items:[],totals:{kcal:0,protein:0,carbs:0,fat:0}};
let toastTimer;
const fmt=v=>Number(v||0).toLocaleString('en-IN',{maximumFractionDigits:1});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(s){$('#toast').textContent=s;$('#toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('show'),3200)}
function tab(name){$$('.tab').forEach(e=>e.classList.toggle('visible',e.id==='tab-'+name));$$('[data-tab]').forEach(e=>e.classList.toggle('active',e.dataset.tab===name));window.scrollTo({top:0,behavior:'smooth'});if(name==='history')loadDay()}
$$('[data-tab]').forEach(e=>e.onclick=()=>tab(e.dataset.tab));['heroScan','sidebarScan','emptyAdd','addHistory'].forEach(x=>$('#'+x).onclick=()=>tab('scan'));$('#viewHistory').onclick=()=>tab('history');
$('#headerDate').textContent=new Date().toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
$('#historyDate').textContent=$('#headerDate').textContent;
function showGoal(){ $('#setKcal').value=goals.kcal;$('#setProtein').value=goals.protein; $('#kcalGoal').textContent='of '+fmt(goals.kcal);$('#proteinGoal').textContent='of '+fmt(goals.protein)+' g'}
showGoal();
$('#saveGoals').onclick=()=>{let k=Number($('#setKcal').value),p=Number($('#setProtein').value);if(k<500||k>10000||p<1||p>500){toast('Enter valid targets.');return}goals={kcal:k,protein:p};localStorage.setItem('reliv_goals',JSON.stringify(goals));showGoal();updateCards();toast('Daily targets saved on this device')};
async function api(path,opt={}){const res=await fetch(path,{...opt,headers:{'Content-Type':'application/json',...(externalSession?.token?{'Authorization':'Bearer '+externalSession.token}:{}),...(opt.headers||{})}});let data=await res.json().catch(()=>({}));if(!res.ok)throw new Error(data.detail||'Request failed');return data}
async function loadDay(){try{currentDay=await api('/api/day?profile='+encodeURIComponent(profile)+'&date='+today()+'&offset_minutes='+new Date().getTimezoneOffset());updateCards();renderMeals()}catch(e){toast(e.message)}}
function updateCards(){const t=currentDay.totals;for(let [key,limit] of [['kcal',goals.kcal],['protein',goals.protein],['carbs',250],['fat',65]]){$('#'+key+'Total').textContent=fmt(t[key]);$('#'+key+'Bar').style.width=Math.min(100,(t[key]||0)/limit*100)+'%'}}
function mealHtml(m){return `<div class="meal-row"><div class="meal-info"><div class="meal-symbol">${iconFor(m.food_name)}</div><div><strong>${esc(m.food_name)}</strong><small>${esc(m.meal)} · ${fmt(m.grams)}${esc(m.unit||"g")}${m.served_amount && m.consumed_percent < 100?` eaten of ${fmt(m.served_amount)}${esc(m.unit||"g")} served`:''}</small><small>${esc(quantityLabel(m.quantity_basis))} · ${esc(m.nutrition_quality?.label||'Nutrition source not reviewed')}</small></div></div><div class="meal-nutri"><b>${fmt(m.kcal)} kcal</b> · ${fmt(m.protein)}g protein <button class="remove-btn" data-remove="${esc(m.id)}" aria-label="Delete meal">×</button></div></div>`}
function iconFor(name){name=name.toLowerCase();if(/pizza|pasta|lasagna/.test(name))return '🍕';if(/chicken|mutton|fish|egg/.test(name))return '🍗';if(/rice|biryani|pulao|chawal/.test(name))return '🍚';if(/fruit|banana|mango|apple/.test(name))return '🍎';if(/shake|milk|coffee|chai|juice/.test(name))return '🥛';return '🍛'}
function renderMeals(){const arr=currentDay.items;$('#todayMeals').innerHTML=arr.length?arr.slice(0,4).map(mealHtml).join(''):`<div class="empty-icon">♧</div><strong>Make your first food entry</strong><p>Scan a meal or find your food to start tracking.</p><button class="outline" id="emptyAdd">+ Log a meal</button>`;if(!arr.length)$('#emptyAdd').onclick=()=>tab('scan');$('#historyItems').innerHTML=arr.length?arr.map(mealHtml).join(''):'<div class="analysis-empty"><strong>No meals logged today</strong><p>Go to Scan to add your first meal.</p></div>';$$('[data-remove]').forEach(b=>b.onclick=async()=>{try{await api('/api/log/'+b.dataset.remove+'?profile='+encodeURIComponent(profile),{method:'DELETE'});await loadDay();toast('Meal removed')}catch(e){toast(e.message)}})}
function nutrition(f,g){let k=g/100;return {kcal:f.kcal*k,protein:f.protein*k,carbs:f.carbs*k,fat:f.fat*k}}
async function loadCatalog(q=''){try{let r=await api('/api/foods?q='+encodeURIComponent(q)+'&limit=60');foods=r.items;$('#catalogCount').textContent=q?`${foods.length} matches`:`${foods.length}+ catalog foods`;$('#suggestions').innerHTML=foods.map(f=>`<button class="food-tile" data-food="${esc(f.id)}"><div class="food-bubble">${iconFor(f.name)}</div><div><strong>${esc(f.name)}</strong><span>${esc(f.category)} · ${fmt(f.kcal)} kcal/100${['Drinks','Mocktails'].includes(f.category)?'ml':'g'}</span></div></button>`).join('')||'<p class="microcopy">No matches. Try another dish spelling.</p>';$$('[data-food]').forEach(b=>b.onclick=()=>{let f=foods.find(x=>x.id===b.dataset.food);addResult(f,f.default_grams,'manual');tab('scan')})}catch(e){toast(e.message)}}
let searchTime;$('#foodSearch').oninput=e=>{clearTimeout(searchTime);searchTime=setTimeout(()=>loadCatalog(e.target.value),200)};
function addResult(food,grams,method='manual',range=null,region=null){results.push({id:crypto.randomUUID?.()||String(Math.random()),food,grams:Number(grams)||food.default_grams,method,range,region,leftover_amount:null,quantity_basis:method==='manual'?'manual_estimate':method==='uncalibrated_photo_estimate'?'visual_estimate':'typical_serving',confirmed:method==='manual',meal:'Breakfast',consumed_percent:100});renderResults();$('#analysisResults').scrollIntoView({block:'nearest',behavior:'smooth'})}
const foodUnit=food=>['Drinks','Mocktails'].includes(food.category)?'ml':'g';
const eatenQuantity=r=>r.leftover_amount===null?r.grams*r.consumed_percent/100:r.grams-r.leftover_amount;
function portionPayload(r){return {grams:r.grams,consumed_percent:r.leftover_amount===null?r.consumed_percent:100,leftover_amount:r.leftover_amount,quantity_basis:r.quantity_basis,unit:foodUnit(r.food)}}
const quantityLabel=b=>({scale:'Weighed on a scale (user-reported)',measuring_container:'Measured volume (user-reported)',label:'Package serving (user-reported)',manual_estimate:'Quantity estimated by you',visual_estimate:'Unweighed photo estimate',typical_serving:'Typical serving, not measured',unspecified:'Quantity source not recorded'}[b]||'Quantity source not recorded');
function renderResults(){$('#resultCount').textContent=results.length+' items';$('#logAllBtn').disabled=!results.length||results.some(r=>!r.confirmed);$('#analysisResults').className=results.length?'':'analysis-empty';$('#analysisResults').innerHTML=results.length?results.map((r,i)=>{let n=nutrition(r.food,eatenQuantity(r));return `<div class="result"><div class="result-top"><div><strong>${esc(r.food.name)}</strong>${r.region?`<span class="demo-chip">Region ${r.region}</span>`:''}<div class="result-details">${r.method==='manual'?'Manually selected':r.method==='uncalibrated_photo_estimate'?'Unweighed AI weight estimate':r.method==='admin_recorded_for_identical_photo'?'Admin-recorded grams for SAME photo; verify your portion':r.method==='similar_reference_user_selected'?'Visually similar admin reference; weight NOT measured':r.method==='user_quantity_required'?'Selected food region · enter edible quantity':'Typical serving (not weighed)'} · Confirm the amount</div></div><button data-del="${i}">Remove</button></div>${r.range?`<div class="result-details">AI portion range: ${fmt(r.range[0])}–${fmt(r.range[1])}g (uncertain)</div>`:''}<div class="gram-line"><input aria-label="Serving quantity in grams or millilitres" type="number" min="1" max="5000" step="1" data-grams="${i}" value="${r.grams}"><span style="font-size:11px;color:#aaa">${['Drinks','Mocktails'].includes(r.food.category)?'ml':'grams'}</span><select data-meal="${i}">${['Breakfast','Lunch','Dinner','Snacks'].map(m=>`<option ${m===r.meal?'selected':''}>${m}</option>`).join('')}</select></div><div class="gram-line"><label style="font-size:12px">Amount eaten <select data-consumed="${i}" aria-label="How much of this serving was eaten">${[100,75,50,25].map(p=>`<option value="${p}" ${p===(r.consumed_percent||100)?'selected':''}>${p===100?'All':p===75?'Three-quarters':p===50?'Half':'Quarter'} (${p}%)</option>`).join('')}</select></label></div><div class="result-details">Nutrition based on ${fmt(eatenQuantity(r))}${['Drinks','Mocktails'].includes(r.food.category)?'ml':'g'} actually eaten, not just served</div><div class="gram-line"><label>Quantity source<select data-basis="${i}">${[['typical_serving','Typical serving'],['manual_estimate','My estimate'],['visual_estimate','Photo estimate'],...(foodUnit(r.food)==='g'?[['scale','Kitchen scale']]:[['measuring_container','Measured liquid volume']]),['label','Package serving']].map(([v,l])=>`<option value="${v}" ${r.quantity_basis===v?'selected':''}>${l}</option>`).join('')}</select></label><label>Left over (${foodUnit(r.food)}, optional)<input data-leftover="${i}" type="number" min="0" max="${r.grams}" step="0.1" value="${r.leftover_amount??''}" placeholder="Leave blank to use % eaten"></label></div><p class="microcopy">${esc(quantityLabel(r.quantity_basis))}. Leftovers must exclude bones, containers and other inedible material. Use either leftover amount or % eaten.</p><div class="result-macros"><span>${fmt(n.kcal)} kcal</span><span>${fmt(n.protein)}g protein</span><span>${fmt(n.carbs)}g carbs</span></div><div class="result-details">${esc(r.food.nutrition_quality?.label || (r.food.source?.startsWith('admin_reviewed:')?'Admin-reviewed recipe example':'Starter estimate'))} · cooking oil and recipes vary</div><button class="outline small" data-usual="${i}">Save as usual</button><label class="user-feedback-check"><input type="checkbox" data-confirm="${i}" ${r.confirmed?'checked':''}> I checked this food, recipe and edible quantity. Nutrition may still be approximate.</label><button class="add" data-add="${i}" ${r.confirmed?'':'disabled'}>✓ Confirm & log meal</button></div>`}).join(''):`<div class="empty-icon">◈</div><strong>Your results will appear here</strong><p>Try a photo, or search for a food below.</p>`;
$$('[data-basis]').forEach(b=>b.onchange=()=>{const r=results[+b.dataset.basis];r.quantity_basis=b.value;r.confirmed=false;renderResults()});
$$('[data-leftover]').forEach(b=>b.onchange=()=>{const r=results[+b.dataset.leftover],value=b.value.trim()===''?null:Number(b.value);if(value!==null&&(!Number.isFinite(value)||value<0||value>=r.grams)){toast('Leftovers must be less than the served edible amount. Remove an uneaten item.');renderResults();return}r.leftover_amount=value;r.consumed_percent=100;r.confirmed=false;renderResults()});
$$('[data-confirm]').forEach(b=>b.onchange=()=>{results[+b.dataset.confirm].confirmed=b.checked;renderResults()});
$$('[data-usual]').forEach(b=>b.onclick=async()=>{const r=results[+b.dataset.usual];if(!r)return;try{await api('/api/me/shortcuts',{method:'POST',body:JSON.stringify({profile,food_id:r.food.id,serving_amount:r.grams,nickname:r.food.name})});await loadUsuals();toast('Saved as a usual meal. Review portions when reusing.')}catch(e){toast(e.message)}});$$('[data-meal]').forEach(b=>b.onchange=()=>{results[+b.dataset.meal].meal=b.value});$$('[data-consumed]').forEach(b=>b.onchange=()=>{results[+b.dataset.consumed].consumed_percent=Number(b.value);results[+b.dataset.consumed].leftover_amount=null;results[+b.dataset.consumed].confirmed=false;renderResults()});$$('[data-del]').forEach(b=>b.onclick=()=>{results.splice(+b.dataset.del,1);renderResults()});$$('[data-grams]').forEach(b=>b.onchange=()=>{let grams=Number(b.value);if(!Number.isFinite(grams)||grams<=0||grams>5000){toast('Enter an amount between 1 and 5000 (g or ml).');b.value=results[b.dataset.grams].grams;return}if(results[b.dataset.grams].leftover_amount!==null&&results[b.dataset.grams].leftover_amount>=grams){toast('Served amount must exceed leftovers');renderResults();return}results[b.dataset.grams].grams=grams;results[b.dataset.grams].confirmed=false;renderResults()});$$('[data-add]').forEach(b=>b.onclick=async()=>{let idx=+b.dataset.add,r=results[idx],meal=$(`[data-meal="${idx}"]`).value;if(!r.confirmed){toast('Confirm the food and quantity first');return}try{await api('/api/log',{method:'POST',body:JSON.stringify({profile,food_id:r.food.id,...portionPayload(r),meal})});results.splice(idx,1);renderResults();await loadDay();toast(`${r.food.name} added to your food diary`)}catch(e){toast(e.message)}})
}
$('#fileInput').onchange=e=>{chosenFile=e.target.files[0];if(!chosenFile)return;if(chosenFile.size>7_000_000){toast('Image must be under 7MB');chosenFile=null;return}$('#preview').src=URL.createObjectURL(chosenFile);$('#preview').hidden=false;resetRegions();$('#analyzeBtn').disabled=false;$('#scanStatus').textContent=''};
$('#analyzeBtn').onclick=async()=>{if(!chosenFile)return;$('#fileInput').disabled=true;$('#scanStatus').textContent='Analysing image…';$('#analyzeBtn').disabled=true;try{const b64=await new Promise((ok,err)=>{let r=new FileReader();r.onload=()=>ok(r.result);r.onerror=err;r.readAsDataURL(chosenFile)});let second=sideFile?await new Promise((ok,err)=>{let r=new FileReader();r.onload=()=>ok(r.result);r.onerror=err;r.readAsDataURL(sideFile)}):null;
let diameter=$('#plateDiameter').value?Number($('#plateDiameter').value):null;
let data=await api('/api/analyze',{method:'POST',body:JSON.stringify({image_base64:b64,secondary_image_base64:second,plate_diameter_cm:diameter,regions:photoRegions})});$('#scanStatus').textContent=data.message||'';
const hints=data.reference_candidates||[];
$('#referenceCandidates').innerHTML=hints.length?`<p class="microcopy">Similar admin photos (NOT guaranteed same food/recipe). Select only after confirming:</p>`+hints.map((h,i)=>`<button class="food-tile" data-reference-candidate="${i}"><span class="food-bubble">🍛</span><span><strong>${esc(h.food.name)}</strong><span>Weight unknown · manually confirm quantity</span></span></button>`).join(''):'';
$$('[data-reference-candidate]').forEach(b=>b.onclick=()=>{const h=hints[+b.dataset.referenceCandidate];if(h?.food){addResult(h.food,h.food.default_grams,'similar_reference_user_selected');toast('Check recipe and grams; this is only a visual suggestion.')}});
const unmatched=(data.items||[]).filter(item=>!item.food);
$('#referenceCandidates').insertAdjacentHTML('beforeend', unmatched.map((item,i)=>`<div class="product-item"><strong>${item.region?'Region '+item.region+': ':''}${esc(item.detected_name)}</strong><p>Choose the actual dish, or search below if none match.</p>${(item.candidates||[]).map((f,j)=>`<button class="outline small" data-match="${i}:${j}">${esc(f.name)}</button>`).join('')}</div>`).join(''));
$$('[data-match]').forEach(button=>button.onclick=()=>{const [i,j]=button.dataset.match.split(':').map(Number),item=unmatched[i];addResult(item.candidates[j],item.candidates[j].default_grams,'user_quantity_required',null,item.region);button.closest('.product-item').remove()});
let n=0;for(const item of data.items||[]){if(item.food){addResult(item.food,item.grams||item.food.default_grams,item.portion_method||'default_serving',item.min_grams&&item.max_grams?[item.min_grams,item.max_grams]:null,item.region);n++}}if(data.items?.length>n){const missing=data.items.filter(x=>!x.food).map(x=>x.detected_name).join(', ');$('#scanStatus').textContent=(data.message||'')+' Unmatched: '+missing+'. Search manually.';toast('Some foods need manual matching.')}else if(n)toast(n+' food items identified. Verify their weights before saving.')}catch(e){$('#scanStatus').textContent=e.message;toast('AI scan unavailable. You can still search and log meals.')}finally{$('#analyzeBtn').disabled=false;$('#fileInput').disabled=false}};
$('#sideInput').onchange=e=>{sideFile=e.target.files[0]||null; if(!sideFile){$('#sidePreview').hidden=true;return} if(sideFile.size>7_000_000){toast('Second photo must be under 7MB');sideFile=null;return}$('#sidePreview').src=URL.createObjectURL(sideFile);$('#sidePreview').hidden=false};
async function showModelState(){
 try{
  let m=await api('/api/model-info');
  if(m.ready){
    $('#visionState').innerHTML=`Camera AI active: <strong>${esc(m.provider)}</strong> (${esc(m.model)}) · ready to scan`;
    $('#visionState').classList.add('ready');
  } else {
    $('#visionState').innerHTML=`Camera AI not active. <div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap"><input id="groqKeyInput" placeholder="Paste free Groq API key (gsk_...)" style="padding:6px 10px;font-size:12px;border:1px solid #ccc;border-radius:6px;flex:1;min-width:180px"><button id="saveGroqKeyBtn" class="outline small" type="button" style="padding:6px 12px;font-size:12px;background:#38a169;color:#fff;border-color:#38a169">Activate Scan</button></div><small style="display:block;margin-top:5px;color:#666">Get a free key from <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" style="color:#2b6cb0;text-decoration:underline">console.groq.com/keys</a></small>`;
    $('#visionState').classList.remove('ready');
    const saveBtn=$('#saveGroqKeyBtn');
    if(saveBtn){
      saveBtn.onclick=async()=>{
        const k=$('#groqKeyInput').value.trim();
        if(!k.startsWith('gsk_')){toast('Key should start with gsk_');return}
        saveBtn.disabled=true;
        try{
          await api('/api/settings/groq-key',{method:'POST',body:JSON.stringify({key:k})});
          toast('Groq AI activated! You can now scan food.');
          await showModelState();
        }catch(err){toast(err.message)}finally{saveBtn.disabled=false}
      };
    }
  }
 }catch(e){
  $('#visionState').textContent='Could not check AI status; manual logging available.';
 }
}
showModelState();
loadCatalog();loadDay();renderResults();
if('serviceWorker' in navigator&&location.protocol==='https:')navigator.serviceWorker.register('/sw.js').catch(()=>{});

// Branded packaged-food lookup: requires a concrete community label, never fuzzy
// substitution of a manufacturer's nutrition facts from a generic food.
let packaged=[],groqResults=[],scannerStream=null,scannerLoop=null;
const productStatus=s=>$('#productStatus').textContent=s;
function renderPackaged(){
 const allItems=[...packaged.map((p,i)=>({type:'off',data:p,idx:i})),...groqResults.map((g,i)=>({type:'groq',data:g,idx:i}))];
 $('#productResults').innerHTML=allItems.length?allItems.map((item,i)=>{
   if(item.type==='off'){
     const p=item.data;
     return `<div class="product-item"><div class="product-title"><strong>${esc(p.brand)} ${esc(p.name)}</strong><small>${esc(p.barcode)} · ${esc(p.nutrition_basis)}</small></div><p>${p.complete?`${fmt(p.kcal)} kcal · ${fmt(p.protein)}g protein · ${fmt(p.carbs)}g carbs · ${fmt(p.fat)}g fat per 100${esc(p.unit)}`:`Missing label values: ${esc(p.missing.join(', '))}`}</p><div class="product-controls"><input data-product-amount="${item.idx}" type="number" min="1" max="5000" step="1" value="${p.unit==='ml'?250:100}" aria-label="Amount ${esc(p.unit)}"><span>${esc(p.unit)}</span><select data-product-meal="${item.idx}">${['Breakfast','Lunch','Dinner','Snacks'].map(m=>`<option>${m}</option>`).join('')}</select><button class="add" data-product-log="${item.idx}" ${p.complete?'':'disabled'}>Log</button></div><p class="microcopy">Source: Open Food Facts · check your product label</p></div>`;
   } else {
     const g=item.data;
     return `<div class="product-item" style="border-color:#38a169"><div class="product-title"><strong>⚡ ${esc(g.brand)} ${esc(g.product_name)}</strong><small>${esc(g.notes || 'Groq AI online label match')} · per 100${esc(g.unit)}</small></div><p>${fmt(g.per_100.kcal)} kcal · ${fmt(g.per_100.protein)}g protein · ${fmt(g.per_100.carbs)}g carbs · ${fmt(g.per_100.fat)}g fat per 100${esc(g.unit)}</p><div class="product-controls"><input data-groq-amount="${item.idx}" type="number" min="1" max="5000" step="1" value="${g.serving_size||(g.unit==='ml'?250:100)}" aria-label="Amount ${esc(g.unit)}"><span>${esc(g.unit)}</span><select data-groq-meal="${item.idx}">${['Breakfast','Lunch','Dinner','Snacks'].map(m=>`<option>${m}</option>`).join('')}</select><button class="add" data-groq-log="${item.idx}">Log Groq Item</button></div><p class="microcopy">Source: ${esc(g.source)} · verify against physical bottle/packet</p></div>`;
   }
 }).join(''):'<p class="microcopy">No products selected. Search a brand, enter a barcode, or use Groq Online.</p>';

 $$('[data-product-log]').forEach(btn=>btn.onclick=async()=>{
  const i=+btn.dataset.productLog,p=packaged[i],amount=Number($(`[data-product-amount="${i}"]`).value),meal=$(`[data-product-meal="${i}"]`).value;
  if(!Number.isFinite(amount)||amount<=0||amount>5000){toast('Enter a valid serving quantity');return;}
  btn.disabled=true;
  try{await api('/api/products/log',{method:'POST',body:JSON.stringify({profile,barcode:p.barcode,amount,meal})});await loadDay();toast('Packaged food logged from product label');productStatus('Saved: '+p.name)}
  catch(e){toast(e.message);productStatus(e.message)}finally{btn.disabled=false;}
 });

 $$('[data-groq-log]').forEach(btn=>btn.onclick=async()=>{
  const i=+btn.dataset.groqLog,g=groqResults[i],amount=Number($(`[data-groq-amount="${i}"]`).value),meal=$(`[data-groq-meal="${i}"]`).value;
  if(!Number.isFinite(amount)||amount<=0||amount>5000){toast('Enter a valid serving quantity');return;}
  btn.disabled=true;
  try{
    await api('/api/products/label/log',{
      method:'POST',
      body:JSON.stringify({
        profile,
        brand:g.brand || 'GroqVerified',
        name:g.product_name,
        amount,
        unit:g.unit,
        per_100:g.per_100,
        meal,
        label_verified_by_user:true
      })
    });
    await loadDay();
    toast(`${g.product_name} logged!`);
    productStatus('Saved: '+g.product_name);
  }catch(e){
    toast(e.message);
    productStatus(e.message);
  }finally{
    btn.disabled=false;
  }
 });
}
$('#searchProductBtn').onclick=async()=>{
 const q=$('#productSearch').value.trim();if(q.length<2){productStatus('Enter at least 2 characters');return}
 productStatus('Searching product labels…');
 try{packaged=(await api('/api/products/search?q='+encodeURIComponent(q))).items;productStatus(`${packaged.length} product variants · verify exact label`);renderPackaged()}
 catch(e){productStatus(e.message);toast('Product search unavailable')}
};
$('#searchGroqBtn').onclick=async()=>{
 const q=$('#productSearch').value.trim();if(q.length<2){productStatus('Enter product name (e.g. Epigamia protein milkshake)');return}
 productStatus('Searching online packaging labels via Groq…');
 $('#searchGroqBtn').disabled=true;
 try{
   const item=await api('/api/groq/product-search',{method:'POST',body:JSON.stringify({query:q})});
   groqResults=[item];
   productStatus(`Found online label for ${item.brand} ${item.product_name}`);
   renderPackaged();
 }catch(e){
   productStatus('Groq search: '+e.message);
   toast('Groq search: '+e.message);
 }finally{
   $('#searchGroqBtn').disabled=false;
 }
};
$('#productSearch').addEventListener('keydown',e=>{if(e.key==='Enter')$('#searchProductBtn').click()});

// Voice transcription via Groq Whisper
let activeRecorder=null,voiceChunks=[];
async function startVoiceInput(targetInput,statusEl,autoSubmitBtn){
 if(activeRecorder&&activeRecorder.state==='recording'){
   activeRecorder.stop();
   return;
 }
 if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined'){
   statusEl.textContent='Voice recording unsupported in this browser';
   return;
 }
 try{
   const stream=await navigator.mediaDevices.getUserMedia({audio:true});
   voiceChunks=[];
   activeRecorder=new MediaRecorder(stream);
   activeRecorder.ondataavailable=e=>{if(e.data.size>0)voiceChunks.push(e.data)};
   activeRecorder.onstop=async()=>{
     stream.getTracks().forEach(t=>t.stop());
     statusEl.textContent='Transcribing speech via Groq Whisper…';
     const blob=new Blob(voiceChunks,{type:'audio/webm'});
     const reader=new FileReader();
     reader.onload=async()=>{
       try{
         const res=await api('/api/groq/transcribe',{
           method:'POST',
           body:JSON.stringify({audio_base64:reader.result,filename:'speech.webm'})
         });
         if(res.text){
           targetInput.value=res.text;
           statusEl.textContent='Recognized: "'+res.text+'"';
           toast('Voice recognized: '+res.text);
           if(autoSubmitBtn)autoSubmitBtn.click();
         }else{
           statusEl.textContent='No speech detected';
         }
       }catch(err){
         statusEl.textContent='Voice transcription: '+err.message;
       }
     };
     reader.readAsDataURL(blob);
   };
   activeRecorder.start();
   statusEl.textContent='🎙️ Listening… click Voice again to stop';
   setTimeout(()=>{if(activeRecorder&&activeRecorder.state==='recording')activeRecorder.stop();},7000);
 }catch(err){
   statusEl.textContent='Microphone permission denied or unavailable';
 }
}
if($('#voiceProductBtn'))$('#voiceProductBtn').onclick=()=>startVoiceInput($('#productSearch'),$('#productStatus'),$('#searchGroqBtn'));
if($('#voiceMealBtn'))$('#voiceMealBtn').onclick=()=>startVoiceInput($('#mealText'),$('#textStatus'),$('#parseTextBtn'));
$('#lookupBarcodeBtn').onclick=async()=>{
 const code=$('#barcodeInput').value.trim();if(!/^\d{8,14}$/.test(code)){productStatus('Barcode must be 8–14 digits');return}
 productStatus('Looking up barcode…');
 try{const p=await api('/api/products/barcode/'+encodeURIComponent(code));packaged=[p];renderPackaged();productStatus('Check label and select serving')}
 catch(e){productStatus(e.message)}
};
const stopScanner=()=>{if(scannerStream)scannerStream.getTracks().forEach(t=>t.stop());scannerStream=null;scannerLoop=null;$('#barcodeVideo').hidden=true;$('#stopBarcodeBtn').hidden=true};
$('#cameraBarcodeBtn').onclick=async()=>{
 if(!window.BarcodeDetector||!navigator.mediaDevices?.getUserMedia){productStatus('Barcode camera scanner unsupported. Enter barcode manually.');return}
 try{
  const detector=new BarcodeDetector({formats:['ean_13','ean_8','upc_a','upc_e']});
  scannerStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
  const video=$('#barcodeVideo');video.srcObject=scannerStream;video.hidden=false;$('#stopBarcodeBtn').hidden=false;await video.play();
  scannerLoop={};const token=scannerLoop;
  const scan=async()=>{if(scannerLoop!==token)return;try{const results=await detector.detect(video);const code=results?.[0]?.rawValue;if(code&&/^\d{8,14}$/.test(code)){$('#barcodeInput').value=code;stopScanner();$('#lookupBarcodeBtn').click();return}}catch(e){productStatus('Could not scan; type barcode instead');stopScanner();return}if(scannerLoop===token)requestAnimationFrame(scan)};
  requestAnimationFrame(scan);
 }catch(e){stopScanner();productStatus('Camera unavailable; enter barcode manually.')}
};
$('#stopBarcodeBtn').onclick=stopScanner;
window.addEventListener('pagehide',stopScanner);
renderPackaged();

$('#logAllBtn').onclick=async()=>{
 if(!results.length)return;
 const btn=$('#logAllBtn');btn.disabled=true;
 if(results.some(r=>!r.confirmed)){toast('Confirm each food and quantity first');return}
 try{const items=results.map((r,i)=>({food_id:r.food.id,...portionPayload(r),meal:$(`[data-meal="${i}"]`).value}));
  await api('/api/log/batch',{method:'POST',body:JSON.stringify({profile,items})});
  const n=results.length;results=[];renderResults();await loadDay();toast(`${n} foods logged together`);
 }catch(e){toast(e.message)}finally{btn.disabled=!results.length||results.some(r=>!r.confirmed);}
};

// Explicitly sourced restaurant profiles. A menu is NOT nutrition evidence.
let restaurantResults=[];
$('#restaurantSearchBtn').onclick=async()=>{
 const q=$('#restaurantSearch').value.trim();if(q.length<2){$('#restaurantStatus').textContent='Enter at least two characters';return}
 try{const j=await api('/api/restaurants?q='+encodeURIComponent(q));restaurantResults=j.items;
 $('#restaurantStatus').textContent=`${restaurantResults.length} menu dishes. Restaurant-specific nutrition is unavailable unless independently verified.`;
 $('#restaurantResults').innerHTML=restaurantResults.map((r,i)=>`<div class="product-item"><div class="product-title"><strong>${esc(r.brand)} · ${esc(r.dish)}</strong><small>${r.advertised_pack_weight_g?`Advertised pack: ${fmt(r.advertised_pack_weight_g)}g · NOT weighed serving`:''}</small></div><p>${r.nutrition_verified_for_specific_dish?'Audited nutrition available':'Restaurant-specific calories/protein not verified'}</p><div class="product-controls"><input data-restaurant-grams="${i}" type="number" min="1" max="5000" value="300" step="10" aria-label="Edible serving grams"><span>g eaten</span><select data-restaurant-meal="${i}">${['Breakfast','Lunch','Dinner','Snacks'].map(m=>`<option>${m}</option>`).join('')}</select><button class="outline" data-restaurant-log="${i}">${r.nutrition_verified_for_specific_dish?'Log verified nutrition':'Log as generic estimate'}</button></div><p class="microcopy"><a href="${esc(r.menu_url)}" target="_blank" rel="noopener noreferrer">Official menu source</a> · confirm edible amount, cooking oil, meat bones and side dishes.</p></div>`).join('')||'<p class="microcopy">No sourced menu dishes matched. Use generic food search or add a verified menu source.</p>';
 $$('[data-restaurant-log]').forEach(btn=>btn.onclick=async()=>{
  const i=+btn.dataset.restaurantLog,r=restaurantResults[i],grams=Number($(`[data-restaurant-grams="${i}"]`).value),meal=$(`[data-restaurant-meal="${i}"]`).value;
  if(!Number.isFinite(grams)||grams<=0||grams>5000){toast('Enter edible serving weight');return}
  if(!r.nutrition_verified_for_specific_dish&&!confirm('Restaurant-specific nutrients are NOT available. Use generic illustrative recipe values? This is NOT measured Arsalan or Biryani By Kilo nutrition.'))return;
  try{const j=await api('/api/restaurants/log',{method:'POST',body:JSON.stringify({profile,brand:r.brand,dish:r.dish,grams,meal,use_generic_estimate:!r.nutrition_verified_for_specific_dish})});await loadDay();toast('Logged with nutrition source: '+j.source);}
  catch(e){toast(e.message)}
 });
 }catch(e){$('#restaurantStatus').textContent=e.message}
};
$('#restaurantSearch').onkeydown=e=>{if(e.key==='Enter')$('#restaurantSearchBtn').click()};
$('#parseTextBtn').onclick=async()=>{
 const text=$('#mealText').value.trim();if(!text){$('#textStatus').textContent='Enter what you ate';return}
 try{const j=await api('/api/parse-meal',{method:'POST',body:JSON.stringify({text})});
  $('#textStatus').textContent='Suggestions only — confirm all foods and quantities.';
  $('#textResults').innerHTML=j.items.map((r,i)=>{
   const name=r.food?.name||r.query||r.brand||'Unrecognized';
   const detail=r.kind==='generic_food'?`${r.grams||'Unknown'} ${r.unit||'g'} · illustrative nutrition`:r.message||'Confirm variant';
   return `<div class="product-item"><div class="product-title"><strong>${esc(name)}</strong><small>${esc(detail)}</small></div>${r.kind==='generic_food'?`<button class="outline" data-text-add="${i}">Review portion and log</button>`:r.kind==='ambiguous'?`<p>${(r.candidates||[]).map(x=>esc(x.name)).join(' · ')}</p><button class="outline" data-text-search="${i}">Choose exact variety</button>`:r.kind==='branded_product_or_restaurant'?`<button class="outline" data-text-search="${i}">Find exact brand / restaurant</button>`:''}</div>`;
  }).join('');
  $$('[data-text-add]').forEach(b=>b.onclick=()=>{let r=j.items[+b.dataset.textAdd];addResult(r.food,r.grams||r.food.default_grams,r.grams?'manual':'default_serving')});
  $$('[data-text-search]').forEach(b=>b.onclick=()=>{
    let r=j.items[+b.dataset.textSearch];if(r.kind==='ambiguous'){$('#foodSearch').value=r.query;loadCatalog(r.query);$('#foodSearch').scrollIntoView({block:'center',behavior:'smooth'})}
    else if(/arsalan|kareem|biryani by kilo/i.test(r.query)){$('#restaurantSearch').value=r.query;$('#restaurantSearchBtn').click();$('#restaurantSearch').scrollIntoView({block:'center',behavior:'smooth'})}
    else{$('#productSearch').value=r.query;$('#searchProductBtn').click();$('#productSearch').scrollIntoView({block:'center',behavior:'smooth'})}
  });
 }catch(e){$('#textStatus').textContent=e.message}
};
$('#mealText').onkeydown=e=>{if(e.key==='Enter')$('#parseTextBtn').click()};

// Reference-quality nutrition for exact USDA record, not heuristic recipe mapping.
let fdcResults=[];
$('#referenceSearchBtn').onclick=async()=>{
 const q=$('#referenceSearch').value.trim();if(q.length<2){$('#referenceStatus').textContent='Enter a food name';return}
 try{const j=await api('/api/reference-foods?q='+encodeURIComponent(q));fdcResults=j.items;
 $('#referenceStatus').textContent=`${fdcResults.length} sourced records · select exact preparation`;
 $('#referenceResults').innerHTML=fdcResults.map((r,i)=>`<div class="product-item"><div class="product-title"><strong>${esc(r.name)}</strong><small>USDA ${esc(r.category)} · ID ${esc(r.fdc_id)}</small></div><p>${fmt(r.per_100g.kcal)} kcal · ${fmt(r.per_100g.protein)} g protein / 100g</p><div class="product-controls"><input data-fdc-grams="${i}" type="number" min="1" max="5000" step="10" value="100" aria-label="Food weight grams"><span>grams</span><select data-fdc-meal="${i}">${['Breakfast','Lunch','Dinner','Snacks'].map(m=>`<option>${m}</option>`).join('')}</select><button class="outline" data-fdc-log="${i}">Log USDA food</button></div><p class="microcopy"><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Reference data</a> · raw vs cooked matters</p></div>`).join('')||'<p class="microcopy">No complete USDA nutrient records found.</p>';
 $$('[data-fdc-log]').forEach(b=>b.onclick=async()=>{
  const i=+b.dataset.fdcLog,r=fdcResults[i],grams=Number($(`[data-fdc-grams="${i}"]`).value),meal=$(`[data-fdc-meal="${i}"]`).value;
  if(!Number.isFinite(grams)||grams<=0||grams>5000){toast('Enter valid grams');return}
  try{await api('/api/reference-foods/log',{method:'POST',body:JSON.stringify({profile,fdc_id:r.fdc_id,grams,meal})});await loadDay();toast('Logged from USDA: '+r.name)}catch(e){toast(e.message)}
 });
 }catch(e){$('#referenceStatus').textContent=e.message}
};
$('#referenceSearch').onkeydown=e=>{if(e.key==='Enter')$('#referenceSearchBtn').click()};

// Explicit opt-in corrections; never auto-train a model from unreviewed user data.
$('#submitFeedback').onclick=async()=>{
 const corrected_name=$('#correctFoodName').value.trim(),grams=$('#correctFoodWeight').value.trim();
 if(corrected_name.length<2){$('#feedbackStatus').textContent='Enter a food name';return}
 if(!$('#feedbackConsent').checked){$('#feedbackStatus').textContent='Consent is required to send data to admin review';return}
 const btn=$('#submitFeedback');btn.disabled=true;
 try{
  const photo=$('#feedbackPhoto').checked&&chosenFile?await new Promise((ok,err)=>{const r=new FileReader();r.onload=()=>ok(r.result);r.onerror=err;r.readAsDataURL(chosenFile)}):null;
  const payload={profile,corrected_name,corrected_grams:grams?Number(grams):null,
    comment:$('#correctFoodNote').value.trim(),reference_id:null,consent_to_admin_review:true,consent_to_reference_training:!!photo&&$('#feedbackTraining').checked,image_base64:photo};
  const res=await api('/api/learning/feedback',{method:'POST',body:JSON.stringify(payload)});
  $('#feedbackStatus').textContent=res.note||'Submitted for admin review';
  toast('Correction submitted for human review');
 }catch(e){$('#feedbackStatus').textContent=e.message}finally{btn.disabled=false}
};

// Optional convenience; never creates an admin-learning dependency.
async function loadUsuals(){
 try{const data=await api('/api/me/shortcuts?profile='+encodeURIComponent(profile));
 $('#usualMeals').innerHTML=data.items.length?data.items.map((x,i)=>`<div class="product-item"><div class="product-title"><strong>${esc(x.nickname)}</strong><small>${esc(x.food_name)} · usual ${fmt(x.serving_amount)}${esc(x.unit)}</small></div><div class="product-controls"><select data-usual-factor="${i}"><option value="1">Usual serving</option><option value="0.5">Half</option><option value="1.5">1½ servings</option><option value="2">Double</option></select><select data-usual-meal="${i}"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snacks</option></select><button class="outline" data-usual-log="${i}">Log meal</button></div></div>`).join(''):'<p class="microcopy">No saved meals. Select a food, then choose Save as usual.</p>';
 $$('[data-usual-log]').forEach(b=>b.onclick=async()=>{const i=+b.dataset.usualLog,x=data.items[i];try{const factor=Number($(`[data-usual-factor="${i}"]`).value),meal=$(`[data-usual-meal="${i}"]`).value;await api('/api/me/shortcuts/'+encodeURIComponent(x.id)+'/log',{method:'POST',body:JSON.stringify({profile,fraction:factor,meal})});await loadDay();toast('Usual meal logged; nutrition source unchanged')}catch(e){toast(e.message)}});
 }catch(e){$('#usualMeals').textContent='Usual meals unavailable: '+e.message}
}
$('#usualDetails').addEventListener('toggle',e=>{if(e.target.open)loadUsuals()});
$('#savePlate').onclick=async()=>{const value=Number($('#plateDiameter').value);if(!value){$('#plateSavedStatus').textContent='Select a known plate size first';return}try{await api('/api/me/plate',{method:'PUT',body:JSON.stringify({profile,diameter_cm:value,label:'My usual plate'})});$('#plateSavedStatus').textContent='Saved on your profile · still not a weighing scale'}catch(e){$('#plateSavedStatus').textContent=e.message}};
(async()=>{try{const r=await api('/api/me/plate?profile='+encodeURIComponent(profile));if(r.plate){$('#plateDiameter').value=String(r.plate.diameter_cm);$('#plateSavedStatus').textContent='Your saved plate size loaded'}}catch(e){}})();
const readFileAsDataURL=file=>new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(file)});
$('#readNutritionLabel').onclick=async()=>{const f=$('#nutritionLabelPhoto').files[0];if(!f){$('#manualLabelStatus').textContent='Choose the nutrition-panel photo first';return}if(f.size>7000000){$('#manualLabelStatus').textContent='Image too large';return}$('#manualLabelStatus').textContent='Reading draft values. Confirm every number against the packet.';
 try{const r=await api('/api/products/label/read',{method:'POST',body:JSON.stringify({image_base64:await readFileAsDataURL(f)})});$('#manualBrand').value=r.brand;$('#manualProduct').value=r.name;$('#manualUnit').value=r.unit;for(const [key,id] of [['kcal','manualKcal'],['protein','manualProtein'],['carbs','manualCarbs'],['fat','manualFat']])$('#'+id).value=r.per_100[key];$('#confirmLabel').checked=false;$('#manualLabelStatus').textContent='AI draft only: verify printed values and unit before logging.'}catch(e){$('#manualLabelStatus').textContent=e.message+' · You can type the label manually.'}
};
$('#logManualLabel').onclick=async()=>{const per_100={kcal:Number($('#manualKcal').value),protein:Number($('#manualProtein').value),carbs:Number($('#manualCarbs').value),fat:Number($('#manualFat').value)};if(['manualKcal','manualProtein','manualCarbs','manualFat'].some(id=>$('#'+id).value.trim()==='')){$('#manualLabelStatus').textContent='Enter all four printed per-100 values';return}
 try{await api('/api/products/label/log',{method:'POST',body:JSON.stringify({profile,brand:$('#manualBrand').value,name:$('#manualProduct').value,amount:Number($('#manualAmount').value),unit:$('#manualUnit').value,per_100,meal:$('#manualMeal').value,label_verified_by_user:$('#confirmLabel').checked})});await loadDay();toast('Label-checked food logged');$('#manualLabelStatus').textContent='Saved as unverified user-entered package label.'}catch(e){$('#manualLabelStatus').textContent=e.message}
};

// Regions are normalized against the oriented browser image; never infer grams from area.
let photoRegions=[],regionStart=null;
const regionCanvas=$('#regionCanvas'),regionContext=regionCanvas.getContext('2d');
function drawRegions(draft=null){
 const im=$('#preview');if(!im.naturalWidth)return;
 regionCanvas.width=Math.min(900,im.naturalWidth);regionCanvas.height=Math.round(regionCanvas.width*im.naturalHeight/im.naturalWidth);
 regionContext.drawImage(im,0,0,regionCanvas.width,regionCanvas.height);
 [...photoRegions,...(draft?[draft]:[])].forEach((r,i)=>{regionContext.strokeStyle='#ff6b00';regionContext.lineWidth=3;regionContext.strokeRect(r.x1*regionCanvas.width,r.y1*regionCanvas.height,(r.x2-r.x1)*regionCanvas.width,(r.y2-r.y1)*regionCanvas.height);regionContext.fillStyle='#fff';regionContext.fillRect(r.x1*regionCanvas.width,r.y1*regionCanvas.height,28,24);regionContext.fillStyle='#111';regionContext.font='bold 18px sans-serif';regionContext.fillText(String(i+1),r.x1*regionCanvas.width+5,r.y1*regionCanvas.height+19)});
 $('#regionStatus').textContent=photoRegions.length?photoRegions.length+' regions selected; each will be analysed separately.':'No regions selected: analyse the whole image.';
}
function resetRegions(){photoRegions=[];regionStart=null;$('#regionTools').hidden=false;$('#preview').onload=()=>{$('#preview').hidden=true;drawRegions()};if($('#preview').complete){$('#preview').hidden=true;drawRegions()}}
function appendRegion(r){if($('#analyzeBtn').disabled)return;if(photoRegions.length>=6){toast('Select up to 6 regions');return}if(!Object.values(r).every(v=>Number.isFinite(v)&&v>=0&&v<=1)||r.x2-r.x1<.02||r.y2-r.y1<.02){toast('Select a larger region inside the image');return}photoRegions.push(r);drawRegions()}
function regionPoint(e){const b=regionCanvas.getBoundingClientRect();return {x:Math.max(0,Math.min(1,(e.clientX-b.left)/b.width)),y:Math.max(0,Math.min(1,(e.clientY-b.top)/b.height))}}
function regionBox(a,b){return {x1:Math.min(a.x,b.x),y1:Math.min(a.y,b.y),x2:Math.max(a.x,b.x),y2:Math.max(a.y,b.y)}}
regionCanvas.onpointerdown=e=>{if($('#analyzeBtn').disabled)return;regionStart=regionPoint(e);regionCanvas.setPointerCapture(e.pointerId)};
regionCanvas.onpointermove=e=>{if(regionStart)drawRegions(regionBox(regionStart,regionPoint(e)))};
regionCanvas.onpointerup=e=>{if(!regionStart)return;const r=regionBox(regionStart,regionPoint(e));regionStart=null;appendRegion(r);drawRegions()};
regionCanvas.onpointercancel=()=>{regionStart=null;drawRegions()};
$('#undoRegion').onclick=()=>{if(!$('#analyzeBtn').disabled){photoRegions.pop();drawRegions()}};
$('#clearRegions').onclick=()=>{if(!$('#analyzeBtn').disabled){photoRegions=[];drawRegions()}};
$('#addRegion').onclick=()=>appendRegion({x1:Number($('#regionLeft').value)/100,y1:Number($('#regionTop').value)/100,x2:Number($('#regionRight').value)/100,y2:Number($('#regionBottom').value)/100});
