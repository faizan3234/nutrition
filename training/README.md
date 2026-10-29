# Training path

### Closed-set food classification

Put your own legally sourced, consented labeled photos under:

```
dataset/classifier/train/<food_name>/image001.jpg
dataset/classifier/val/<food_name>/image999.jpg
```

Use food-disjoint *images of meal instances* across splits to prevent leakage (do not let two photos of the same dish appear in train and validation). Run `pip install tensorflow` then `python -m training.train_classifier --data dataset/classifier`.

### Multi-item recognition

Create YOLO bounding boxes for all visible items of each mixed thali / plate. Use `dataset/yolo/data.yaml` with paths for train/val/test and `names` mapping. Run `pip install ultralytics` then `python -m training.train_detector --data dataset/yolo/data.yaml`. Ultralytics packages have licensing implications: check AGPL/commercial obligations before use.

### Portion-weight learning (not yet supplied)

An image-label dataset alone cannot train a gram estimator. For supervised portion learning record `food_id`, ground truth **weighed grams**, ingredients, vessel dimensions, reference object, focal characteristics, optional depth, image paths and cooking style. Train a separate mass regression head; evaluate on dishes, devices and people **not seen during training**. The current system only scales nutrition after grams are supplied or visually guessed by optional external AI.

Do not show "90% calorie accuracy" based on dish classification accuracy. Benchmark detection/classification, portion MAE, calorie MAE and protein MAE independently.
