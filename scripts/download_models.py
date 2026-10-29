"""Download local vision model weights for Reliv Nutrition AI."""
import json
import urllib.request
from pathlib import Path

MODEL_DIR = Path("models")
MODEL_URL = "https://huggingface.co/onnx-community/swin-finetuned-food101-ONNX/resolve/main/onnx/model_quantized.onnx"
CONFIG_URL = "https://huggingface.co/onnx-community/swin-finetuned-food101-ONNX/raw/main/config.json"


def download():
    MODEL_DIR.mkdir(exist_ok=True)
    model_path = MODEL_DIR / "food_classifier.onnx"
    labels_path = MODEL_DIR / "food_labels.json"

    if not labels_path.is_file():
        print("Downloading food class labels...")
        with urllib.request.urlopen(CONFIG_URL, timeout=30) as res:
            cfg = json.load(res)
        labels = cfg.get("id2label", {})
        labels_path.write_text(json.dumps(labels, indent=2), encoding="utf-8")
        print(f"Saved {len(labels)} food labels to {labels_path}")
    else:
        print(f"Labels file already exists: {labels_path}")

    if not model_path.is_file():
        print("Downloading Food-101 Swin Transformer ONNX model (~93MB)...")
        urllib.request.urlretrieve(MODEL_URL, model_path)
        print(f"Downloaded model to {model_path} ({model_path.stat().st_size / 1_000_000:.1f} MB)")
    else:
        print(f"Model already exists: {model_path} ({model_path.stat().st_size / 1_000_000:.1f} MB)")

    print("\nLocal vision model is ready for Reliv Nutrition AI!")


if __name__ == "__main__":
    download()
