"""User-selected food regions: recognition assistance, never pixel-to-mass conversion."""
import base64
import io
from PIL import Image
from pydantic import BaseModel, Field, model_validator
from .vision import analyze, normalize_image


class PhotoRegion(BaseModel):
    x1: float = Field(ge=0, le=1, allow_inf_nan=False)
    y1: float = Field(ge=0, le=1, allow_inf_nan=False)
    x2: float = Field(ge=0, le=1, allow_inf_nan=False)
    y2: float = Field(ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode='after')
    def valid_area(self):
        if self.x2 - self.x1 < .02 or self.y2 - self.y1 < .02:
            raise ValueError('Select a food region at least 2% wide and tall')
        return self


def analyze_regions(image_b64, regions):
    image = Image.open(io.BytesIO(normalize_image(image_b64)))
    items, reports = [], []
    for index, region in enumerate(regions):
        box = [region.x1, region.y1, region.x2, region.y2]
        crop = image.crop((int(box[0]*image.width), int(box[1]*image.height),
                           int(box[2]*image.width), int(box[3]*image.height)))
        out = io.BytesIO()
        crop.save(out, format='JPEG', quality=95)
        try:
            # Plate diameter/second angle do not describe this cropped coordinate space.
            result = analyze(base64.b64encode(out.getvalue()).decode('ascii'))
            reports.append({'region': index + 1, 'status': result['status']})
            for item in result['items']:
                # Reference-photo mass and provider guesses cannot measure this crop.
                item = {**item, 'region': index + 1, 'bbox': box,
                        'grams': None, 'min_grams': None, 'max_grams': None,
                        'portion_method': 'user_quantity_required',
                        'mass_is_measured': False, 'needs_confirmation': True}
                items.append(item)
        except RuntimeError:
            reports.append({'region': index + 1, 'status': 'unavailable'})
    return {'provider': 'selected_regions', 'status': 'needs_review', 'items': items,
            'regions': reports, 'reference_candidates': [],
            'message': 'Review each selected region. Add missed foods using search. Avoid overlapping regions or counting a complete dish plus its ingredients twice. Enter edible quantity separately; crops cannot measure weight. Failed or empty regions need manual search.'}
