"""Train a YOLO multi-food detector. Check Ultralytics licensing before use.
Usage: python -m training.train_detector --data dataset/yolo/data.yaml
"""
import argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--model',default='yolov8n.pt');p.add_argument('--epochs',type=int,default=50);p.add_argument('--imgsz',type=int,default=640);a=p.parse_args()
    if not Path(a.data).is_file():raise FileNotFoundError(a.data)
    from ultralytics import YOLO
    model=YOLO(a.model)
    result=model.train(data=a.data,epochs=a.epochs,imgsz=a.imgsz,seed=42,project='artifacts',name='multi-food')
    print('Training complete. Evaluate held-out weighed meals separately for gram/protein error.')

if __name__=='__main__':main()
