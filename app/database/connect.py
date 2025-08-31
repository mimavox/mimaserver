import os
from pathlib import Path

from tortoise import Tortoise

# SQLite file under app/ by default
BASE_DIR = Path(__file__).resolve().parents[1]  # .../app
DB_PATH = BASE_DIR / "database/appdata.db"
DB_URL = f"sqlite://{DB_PATH}"

MODELS = {"models": ["database.models"]}

async def connect() -> None:
    await Tortoise.init(db_url=DB_URL, modules=MODELS)

async def disconnect() -> None:
    await Tortoise.close_connections()

async def generate() -> None:
    # Create tables if they don't exist; non-destructive
    await Tortoise.generate_schemas(safe=True)

