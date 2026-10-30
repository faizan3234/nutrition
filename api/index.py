"""Vercel Serverless Function entrypoint for Reliv Nutrition AI."""
import os
import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' and all submodules resolve cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure writable sqlite and temp storage in Vercel serverless environment
os.environ.setdefault("NUTRITION_DB_PATH", "/tmp/nutrition.sqlite3")
os.environ.setdefault("RELIV_LEARNING_IMAGE_DIR", "/tmp/private_learning_images")

os.environ.setdefault("RELIV_ENV", "production")

from app.main import app
