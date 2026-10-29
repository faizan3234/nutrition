// Reliv 7 PWA integration example. The backend is a trusted, separately deployed service.
// Configure CORS_ALLOWED_ORIGINS to your PWA origin. Never put GROQ_API_KEY or server tokens in frontend code.
const NUTRITION_API = '/nutrition-api'; // Preferred: reverse proxy so same-origin auth policies can apply.

async function fileToDataUrl(file) {
  if (!file || !/^image\/(jpeg|png|webp)$/.test(file.type) || file.size > 7_000_000) {
    throw new Error('Select a JPEG, PNG or WebP photo under 7 MB');
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Could not read photograph'));
    reader.readAsDataURL(file);
  });
}

export async function analyseRelivMeal(primaryFile, sideFile = null, plateDiameterCm = null) {
  const body = {
    image_base64: await fileToDataUrl(primaryFile),
    secondary_image_base64: sideFile ? await fileToDataUrl(sideFile) : null,
    plate_diameter_cm: plateDiameterCm,
  };
  const response = await fetch(`${NUTRITION_API}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Food analysis unavailable (${response.status})`);
  const data = await response.json();
  // ALWAYS ask the user to confirm each item and the grams before logging.
  // Do not confuse the food mass with protein mass.
  return data;
}

export async function foodSearch(query) {
  const response = await fetch(`${NUTRITION_API}/api/foods?q=${encodeURIComponent(query)}&limit=60`);
  if (!response.ok) throw new Error('Nutrition catalogue unavailable');
  return (await response.json()).items;
}

// Packaged foods: do not infer a branded drink's nutrition from its name alone.
export async function searchBrandedProducts(query) {
  if (!query || query.trim().length < 2) return [];
  const response = await fetch(`${NUTRITION_API}/api/products/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) throw new Error('Packaged product search unavailable');
  return (await response.json()).items;
}

export async function lookupBrandedBarcode(barcode) {
  if (!/^\d{8,14}$/.test(String(barcode))) throw new Error('Invalid barcode');
  const response = await fetch(`${NUTRITION_API}/api/products/barcode/${barcode}`);
  if (!response.ok) throw new Error('Product not found or lookup unavailable');
  return response.json();
}

// NOTE: demo profile IDs in the prototype are NOT production authentication.
// Replace the demo profile with the Reliv app's verified account identity
// enforced server-side before publishing a live health-history tracker.
export async function logConfirmedMeal(profile, items, relivJwt) {
  const response = await fetch(`${NUTRITION_API}/api/log/batch`, {
    method: 'POST', headers: {'Content-Type':'application/json', 'Authorization': `Bearer ${relivJwt}`},
    body: JSON.stringify({profile,items}),
  });
  if (!response.ok) throw new Error('Meal log failed');
  return response.json();
}

// Verified host application also supplies equivalent bearer token for
// /api/day, /api/products/log, /api/restaurants/log, /api/reference-foods/log.
// In production the server validates HS256 signature, issuer, audience,
// expiry and exact profile. The JWT must be minted by the Reliv auth backend.
// NEVER put RELIV_AUTH_SECRET, GROQ_API_KEY, or FDC_API_KEY in this file.
