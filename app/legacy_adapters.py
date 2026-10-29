"""Optional loaders for weights supplied by the *operator*, subject to their own rights.

This project does not bundle/relicense any upstream weights or copy upstream code.
Provided as independent interoperable adapters for research evaluation.
"""
from functools import lru_cache
from pathlib import Path
import json
import os
import io
from PIL import Image

@lru_cache(maxsize=1)
def _nutrilens_model():
    try:import tensorflow as tf
    except ImportError:raise RuntimeError('TensorFlow is required for the 22-food classifier adapter')
    weights=Path(os.getenv('NUTRILENS_WEIGHTS','models/nutrilens.h5'))
    labels=Path(os.getenv('NUTRILENS_LABELS','models/nutrilens_labels.json'))
    if not weights.is_file() or not labels.is_file():raise RuntimeError('Operator-supplied NutriLens model/labels missing')
    model=tf.keras.models.load_model(str(weights),compile=False)
    mapping=json.loads(labels.read_text())
    return model,{int(k):v for k,v in mapping.items()}

def infer_nutrilens(image:bytes):
    import numpy as np
    model,labels=_nutrilens_model()
    im=Image.open(io.BytesIO(image)).convert('RGB').resize((224,224))
    arr=np.asarray(im,dtype=np.float32)
    # Keras EfficientNet preprocess_input is a no-op for the modern built-in Rescaling layer.
    predictions=model.predict(np.expand_dims(arr,0),verbose=0)[0]
    idx=int(np.argmax(predictions))
    return [{'name':labels[idx].replace('_',' '),'grams':None,'min_grams':None,'max_grams':None,
             'model_score':float(predictions[idx]),'confidence':'low'}]

@lru_cache(maxsize=1)
def _yolo_model():
    try:from ultralytics import YOLO
    except ImportError:raise RuntimeError('Ultralytics not installed; review its license before use')
    file=Path(os.getenv('YOLO_WEIGHTS','models/food_detector.pt'))
    if not file.is_file():raise RuntimeError('Operator-supplied YOLO food detector weights missing')
    return YOLO(str(file))

def infer_yolo(image:bytes):
    import numpy as np
    model=_yolo_model()
    im=Image.open(io.BytesIO(image)).convert('RGB')
    prediction=model.predict(np.asarray(im),conf=0.35,verbose=False)[0]
    names=prediction.names
    out=[]
    for item in prediction.boxes:
        idx=int(item.cls[0]);score=float(item.conf[0])
        out.append({'name':str(names[idx]).replace('_',' '),'grams':None,
                    'min_grams':None,'max_grams':None,'model_score':score,
                    'confidence':'low'})
    return out[:12]

# Exactly the 22 labels of the original NutriLens classifier, as published in its labels.json.
KNOWN_22_LABELS = [
    'biryani','chai','chole_bhature','dhokla','dosa','gulab_jamun',
    'idli','jalebi','kulfi','medu_wada','momos','naan',
    'pakode','paneer','pani_puri','pav_bhaji','poha','rajma_chawal',
    'roll','roti','samosa','vada_pav'
]
