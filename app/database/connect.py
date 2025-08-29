from __future__ import annotations
import os
from pathlib import Path

from tortoise import Tortoise

# SQLite file under app/ by default; override via DB_URL or DB_FILE env vars
BASE_DIR = Path(__file__).resolve().parents[1]  # .../app
DB_PATH = BASE_DIR / os.getenv("DB_FILE", "appdata.db")
DB_URL = os.getenv("DB_URL", f"sqlite://{DB_PATH}")

# Make sure app/models/__init__.py exists and contains your Tortoise models
# MODELS must reference the actual module path where your Tortoise models are defined.
MODELS = {"models": ["database.models"]}

async def connect() -> None:
    await Tortoise.init(db_url=DB_URL, modules=MODELS)

async def disconnect() -> None:
    await Tortoise.close_connections()

async def generate() -> None:
    # Create tables if they don't exist; non-destructive
    await Tortoise.generate_schemas(safe=True)

