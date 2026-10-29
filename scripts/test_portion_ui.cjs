// DOM integration test. Does not substitute for real phone/camera/browser QA.
const {JSDOM}=require('jsdom');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const root=path.join(__dirname,'..');
const dom=new JSDOM(fs.readFileSync(path.join(root,'web/index.html'),'utf8'),{url:'https://reliv.test',runScripts:'outside-only'});
const w=dom.window;
w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
w.HTMLCanvasElement.prototype.getContext=()=>({});
const calls=[];
w.fetch=async(url,options={})=>{calls.push({url,options});let data={items:[]};
 if(url.startsWith('/api/day'))data={items:[],totals:{kcal:0,protein:0,carbs:0,fat:0}};
 if(url.startsWith('/api/model-info'))data={ready:false};
 if(url.startsWith('/api/me/plate'))data={plate:null};
 return {ok:true,json:async()=>data};
};
w.eval(fs.readFileSync(path.join(root,'web/app.js'),'utf8'));
const $=s=>w.document.querySelector(s);
function change(s,value){const e=$(s);e.value=value;e.dispatchEvent(new w.Event('change'));}
function confirm(){const e=$('[data-confirm]');e.checked=true;e.dispatchEvent(new w.Event('change'));}
(async()=>{
 await new Promise(r=>setTimeout(r,0));
 w.addResult({id:'steamed-rice',name:'Steamed Rice',category:'Staples',kcal:130,protein:2.7,carbs:28,fat:.3,default_grams:200,source:'illustrative'},300,'user_quantity_required');
 assert.equal($('#logAllBtn').disabled,true);
 change('[data-leftover]','125');
 change('[data-basis]','scale');
 assert.match($('.result-macros').textContent,/227.5 kcal/);
 assert.match($('.result-macros').textContent,/4.7g protein/);
 confirm();assert.equal($('#logAllBtn').disabled,false);
 change('[data-leftover]','301'); // rejected, preserve valid amount
 assert.equal($('[data-leftover]').value,'125');
 change('[data-grams]','350');
 assert.equal($('#logAllBtn').disabled,true); // amount edit requires re-confirmation
 change('[data-grams]','300');confirm();
 await $('#logAllBtn').onclick();
 const sent=JSON.parse(calls.find(c=>c.url==='/api/log/batch').options.body).items[0];
 assert.deepEqual(sent,{food_id:'steamed-rice',grams:300,consumed_percent:100,leftover_amount:125,quantity_basis:'scale',unit:'g',meal:'Breakfast'});
 w.addResult({id:'milk-whole',name:'Milk',category:'Drinks',kcal:61,protein:3.2,carbs:5,fat:3,default_grams:200,source:'illustrative'},300,'user_quantity_required');
 assert.equal($('[data-basis] option[value="scale"]'),null);
 change('[data-leftover]','50');change('[data-basis]','measuring_container');
 change('[data-consumed]','50');assert.equal($('[data-leftover]').value,'');
 confirm();await $('[data-add]').onclick();
 const single=JSON.parse(calls.find(c=>c.url==='/api/log').options.body);
 assert.equal(single.unit,'ml');assert.equal(single.consumed_percent,50);assert.equal(single.leftover_amount,null);
 assert.equal(single.quantity_basis,'measuring_container');
 console.log('PASS: UI leftovers, totals, confirmation, invalid input, batch payload, liquid units and single log.');
 w.close();
})().catch(e=>{console.error(e);w.close();process.exitCode=1;});
