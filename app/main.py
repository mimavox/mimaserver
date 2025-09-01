import time
import glob
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, HTTPException

from pyvis.network import Network
import cog_graphs.components as components

from actions import Actions
from database.connect import connect, disconnect, generate
import database.models as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect()
    await generate()
    try:
        yield
    finally:
        # Shutdown
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


# ----------------- Routes -----------------

# Test
@app.get("/")
async def root():
    user1 = await db.User.create(user_name="Test")
    # user1 = await db.User.get(name="Andreas")
    
    user1.user_name = "Again"
    await user1.save()
    
    return {"user_name": user1.user_name}

# Get all available modules for the UI
@app.get("/modules")
async def available_modules():
    return components.modules
    

# Login with posted credentials
@app.post("/login")
async def login():
    pass

# Load cog graph "name"
@app.get("/load/{name}")
async def load(name: str):
    pass

# Save posted cog graph "name" (create if not exists)
@app.post("/save/{name}")
async def save(name: str):
    pass

# Run cog graph "name" with posted POV
@app.post("/run/{name}")
async def run(file: UploadFile, name: str):
    result = save_obs_to_disk(file)
    if result != "error":
        # Retrive cog graph "name"
        # Run cog graph with OBS from latest_obs_on_disk()
        # Return result
        
        # Use a component function:
        # print(components.modules["TtI"][3]("sample text"))
        try:
            path = latest_obs_on_disk()
            result = await components.modules["ItT"][3](path)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        result = {"message": "failed to save obs"}
    
    return {"answer": result}



        

# DEPRECATED:
@app.get("/llm")
async def llm():
    result = await agent.run("What is the capital of Sweden?")
    return {"answer": result.output}

@app.get("/send")
async def send():
    result = await obs_upload()
    return {"answer": result.output}

@app.post("/obs")
async def uploadfile(file: UploadFile):
    try:
        os.makedirs("obs", exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H.%M")
        file_path = f"obs/{timestamp}.png"
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return {"message": "obs saved successfully"}
    except Exception as e:
        print("message:", e.args)
        return {"message": "failed to save obs"}

