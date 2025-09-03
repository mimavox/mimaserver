import time
import glob
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, UploadFile, HTTPException, Depends, status

from pyvis.network import Network
import cog_graphs.components as components

from actions import Actions
from database.connect import connect, disconnect, generate
import database.models as db
from session.auth import get_password_hash, verify_password, create_access_token, get_current_user
from session.schemas import UserCreate, LoginRequest, Token

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init DB and create tables
    await connect()
    await generate()
    try:
        yield
    finally:
        # Shutdown: close DB
        await disconnect()

app = FastAPI(lifespan=lifespan)

# Save OBS to disk
def save_obs_to_disk(file: UploadFile) -> str:
    try:
        os.makedirs("obs", exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H.%M")
        file_path = f"obs/{timestamp}.png"
        contents = file.file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return "ok"
    except Exception as e:
        print("message:", e.args)
        return "error"
        #raise HTTPException(status_code=500, detail="Failed to save OBS")

# Get latest OBS from disk
def latest_obs_on_disk() -> str:
    list_of_files = glob.glob("./obs/*")
    if not list_of_files:
        raise FileNotFoundError("No files in ./obs")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


# ----------------- Auth routes -----------------

# Test (no auth)
@app.get("/")
async def root():
    user1 = await db.User.create(user_name="Test")
    # user1 = await db.User.get(name="Andreas")
    
    user1.user_name = "Again"
    await user1.save()
    
    return {"user_name": user1.user_name}

# Create user (no auth)
@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    if await db.User.get_or_none(user_name=payload.user_name):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(payload.password)
    await db.User.create(user_name=payload.user_name, hashed_password=hashed)
    return {"ok": True}

@app.post("/login", response_model=Token)
async def login(payload: LoginRequest):
    user = await db.User.get_or_none(user_name=payload.user_name)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(subject=user.user_name)
    return {"access_token": token, "token_type": "bearer"}

# List available modules (protected)
@app.get("/modules")
async def modules(current_user: db.User = Depends(get_current_user)):
    return components.modules

# Get user profile
@app.get("/profile")
async def profile(current_user: db.User = Depends(get_current_user)):
    print(current_user)
    return current_user


# Load cog graph "name" (protected)
@app.get("/load/{name}")
async def load(name: str, current_user: db.User = Depends(get_current_user)):
    # Example: use current_user to scope data
    # The get_or_none() method in Tortoise ORM is used to retrieve a single object from the database. If no object matches the query, it returns None instead of raising an error. This is a safer alternative to .get() when you are unsure if a record exists.
    # graph = await db.CogModel.get_or_none(model_name=name, owner=current_user)
    # if not graph:
    #     raise HTTPException(status_code=404, detail="Graph not found")
    return {"name": name, "owner": current_user.user_name}

# Save posted cog graph "name" (protected)
@app.post("/save/{name}")
async def save(name: str, current_user: db.User = Depends(get_current_user)):
    # Example:
    # The update_or_create method in Tortoise ORM is a convenience function used to either update an existing object or create a new one if it doesn't exist.
    # payload = await request.json()
    # graph = await db.CogModel.update_or_create(
    #     defaults={"cog_graph": payload},
    #     model_name=name,
    #     owner=current_user,
    # )
    return {"saved": True, "name": name, "owner": current_user.user_name}

# Run cog graph "name" with posted POV (protected)
@app.post("/run/{name}")
async def run(
    file: UploadFile,
    name: str,
    current_user: db.User = Depends(get_current_user),
):
    result = save_obs_to_disk(file)
    if result != "error":
        try:
            path = latest_obs_on_disk()
            # Example: call a component
            result = await components.modules["ItT"][3](path)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        result = {"message": "failed to save obs"}

    return {"answer": result, "owner": current_user.user_name}
