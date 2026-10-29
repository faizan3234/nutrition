"""Optional local CLIP-like visual embedding search; no model weights bundled.

This is retrieval, not reinforcement learning, and cosine score is NOT
classification confidence. Requires operator-licensed, locally staged model.
"""
from __future__ import annotations
import io
import json
import math
import os
from functools import lru_cache
from pathlib import Path
from PIL import Image
from .db import connection


def model_dir():
    return os.getenv('RELIV_SEMANTIC_MODEL_DIR','').strip()


def configured():
    path=model_dir()
    return bool(path) and Path(path).is_dir() and (Path(path)/'config.json').is_file()


@lru_cache(maxsize=1)
def _backend(path:str):
    from transformers import AutoProcessor,CLIPModel
    # Offline/allowlist local weights; do not download or execute remote code.
    processor=AutoProcessor.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    model=CLIPModel.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    model.eval()
    return processor,model


def embed_image(image: bytes) -> list[float]:
    if not configured():raise RuntimeError('Local semantic model not configured')
    import torch
    processor,model=_backend(str(Path(model_dir()).resolve()))
    picture=Image.open(io.BytesIO(image)).convert('RGB')
    inputs=processor(images=picture,return_tensors='pt')
    with torch.inference_mode():
        result=model.get_image_features(**inputs)
    # Transformers versions return either a tensor or a model output.
    if hasattr(result,'pooler_output'):result=result.pooler_output
    if isinstance(result,tuple):result=result[0]
    result=result.float().flatten()
    result=result/torch.linalg.vector_norm(result).clamp_min(1e-12)
    return result.cpu().tolist()


def cosine(a:list[float],b:list[float]) -> float:
    if len(a)!=len(b) or not a:return -1
    da=math.sqrt(sum(x*x for x in a));db=math.sqrt(sum(x*x for x in b))
    if da==0 or db==0:return -1
    return sum(x*y for x,y in zip(a,b))/(da*db)


def update_embedding_index():
    if not configured():raise RuntimeError('Local semantic model directory required')
    # Stored representation remains tied to a specific model directory; retraining
    # or model swap requires rebuilding this index.
    model_key=Path(model_dir()).resolve().name
    from .learning import now
    with connection() as c:
        photos=[dict(row) for row in c.execute('''SELECT DISTINCT p.id,p.image_path
            FROM learning_photos p JOIN learning_examples e ON e.photo_id=p.id WHERE e.status='approved' AND p.rights_attested=1 ''')]
    count=0
    for photo in photos:
        from pathlib import Path
        vector=embed_image(Path(photo['image_path']).read_bytes())
        with connection() as c:
            c.execute('''INSERT INTO learning_embeddings(photo_id,model_key,vector_json,indexed_at) VALUES (?,?,?,?)
                       ON CONFLICT(photo_id,model_key) DO UPDATE SET vector_json=excluded.vector_json,indexed_at=excluded.indexed_at''',
                      (photo['id'],model_key,json.dumps(vector),now()))
        count+=1
    return {'indexed_photos':count,'model_key':model_key}


def candidates(image_bytes:bytes, limit:int=5, minimum_cosine:float=.85):
    """Semantic candidate suggestions only. Threshold is a configurable uncalibrated heuristic."""
    if not configured():return []
    model_key=Path(model_dir()).resolve().name
    with connection() as c:
        rows=[dict(r) for r in c.execute('''SELECT DISTINCT e.*,l.vector_json,l.model_key
            FROM learning_embeddings l JOIN learning_photos p ON p.id=l.photo_id
            JOIN learning_examples e ON e.photo_id=p.id
            WHERE e.status='approved' AND p.rights_attested=1 AND l.model_key=? LIMIT 4000''',(model_key,))]
    if not rows:return []
    query=embed_image(image_bytes)
    out=[]
    for row in rows:
        score=cosine(query,json.loads(row['vector_json']))
        if score>=minimum_cosine:out.append((score,row))
    out.sort(key=lambda x:x[0],reverse=True)
    from .learning import food_object
    seen=set();res=[]
    for sim,row in out:
        identity=(row['name'].casefold(),row['recipe_variant'].casefold())
        if identity in seen:continue
        seen.add(identity)
        res.append({'food':food_object(row),'reference_id':row['id'],'grams':None,
                    'similarity_score_not_probability':round(sim,4),'retrieval_method':'local_semantic_embedding',
                    'warning':'Semantic suggestion, NOT confirmed same recipe or portion; manually check and weigh.'})
        if len(res)>=limit:break
    return res
