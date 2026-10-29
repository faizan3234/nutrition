"""Reliv Nutrition application configuration."""
from pathlib import Path
from dotenv import load_dotenv
# Local development convenience; deployed environment values take precedence.
load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=False)
