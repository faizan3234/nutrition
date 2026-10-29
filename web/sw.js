const CACHE='reliv-nutrition-v4';const ASSETS=['/','/assets/style.css','/assets/app.js','/assets/icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||event.request.url.includes('/api/'))return;event.respondWith(fetch(event.request).catch(()=>caches.match(event.request)))});
