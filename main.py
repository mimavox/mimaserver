from fastapi import FastAPI, UploadFile, HTTPException, Depends, status
from sqlmodel import Field, Session, SQLModel, create_engine, select

import glob
import os
import time


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    password: str

class CogGraph(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    model_name: str = Field(index=True)
    graph_json: str
    owner_id: int = Field(foreign_key="user.id")


engine = create_engine(os.getenv("DATABASE_URL"))

def create_db_and_tables():
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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


# ----------------- Public routes -----------------
@app.get("/")
def main():
    return {"message": "Hello World"}
