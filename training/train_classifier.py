"""Train a NEW closed-set food classifier on locally authorized labeled pictures.
Usage: python -m training.train_classifier --data dataset/classifier --out artifacts
Expected: dataset/classifier/train/FOOD/*.jpg and val/FOOD/*.jpg, disjoint by meal.
Never confuse classification validation accuracy with weight/calorie accuracy.
"""
import argparse,json,random
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',default='artifacts');p.add_argument('--epochs',type=int,default=8);p.add_argument('--batch',type=int,default=24);p.add_argument('--seed',type=int,default=42);a=p.parse_args()
    import numpy as np
    import tensorflow as tf
    random.seed(a.seed);np.random.seed(a.seed);tf.random.set_seed(a.seed)
    root=Path(a.data)
    validation = 'validation' if (root/'validation').is_dir() else 'val'
    for name in ['train',validation]:
        if not (root/name).is_dir():raise FileNotFoundError(root/name)
    tr=tf.keras.utils.image_dataset_from_directory(root/'train',image_size=(224,224),batch_size=a.batch,shuffle=True,seed=a.seed)
    va=tf.keras.utils.image_dataset_from_directory(root/validation,image_size=(224,224),batch_size=a.batch,shuffle=False)
    classes=tr.class_names
    if classes!=va.class_names:raise ValueError('Training and validation class labels differ')
    aug=tf.keras.Sequential([tf.keras.layers.RandomFlip('horizontal'),tf.keras.layers.RandomRotation(.05),tf.keras.layers.RandomZoom(.09)])
    backbone=tf.keras.applications.EfficientNetB0(include_top=False,weights='imagenet',input_shape=(224,224,3),pooling='avg')
    backbone.trainable=False
    model=tf.keras.Sequential([tf.keras.Input((224,224,3)),aug,backbone,tf.keras.layers.Dropout(.3),tf.keras.layers.Dense(len(classes),activation='softmax')])
    model.compile(optimizer=tf.keras.optimizers.Adam(2e-3),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    callbacks=[tf.keras.callbacks.EarlyStopping(patience=3,restore_best_weights=True),tf.keras.callbacks.ModelCheckpoint(str(out/'best.keras'),save_best_only=True,monitor='val_loss')]
    history=model.fit(tr,validation_data=va,epochs=a.epochs,callbacks=callbacks)
    model.save(out/'final.keras')
    (out/'labels.json').write_text(json.dumps(dict(enumerate(classes)),indent=2))
    (out/'training_history.json').write_text(json.dumps(history.history,indent=2))
    print('Validation metrics:',dict(zip(model.metrics_names,model.evaluate(va,verbose=0))))

if __name__=='__main__':main()
