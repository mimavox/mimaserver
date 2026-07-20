from fastapi import FastAPI, UploadFile, HTTPException, Depends, status
import glob
import os

import time

import networkx as nx
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from session.auth import get_password_hash, verify_password, create_access_token, get_current_user
import cog_graphs.components as components

# Database connection
from database.connect import create_engine
from database.connect import create_db_and_tables
from database.models import CogGraph, User

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# DATABASE_URL is set as env variable in fastapi cloud
engine = create_engine(os.getenv("DATABASE_URL"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic goes here
    create_db_and_tables(engine)
    try:
        yield
    finally:
        # shutdown logic (if needed) goes here
        pass

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

@app.get("/")
def main():
    return {"message": "Hello World"}

# Mock test (no auth)
@app.get("/mock")
async def mock():
    # Get user "test". Create if it doesn't exist.
    with Session(engine) as session:
        statement = select(User).where(User.user_name == "test")
        user1 = session.exec(statement).first()
        if not user1:
            user1 = User(user_name="test", password="test")
            session.add(user1)
            session.commit()
            session.refresh(user1)

        # Build a graph.
        DG = nx.DiGraph()
        DG.add_nodes_from(["A", "B", "C"])
        DG.add_edges_from([("A", "B"), ("B", "C")])
        DG_data = nx.node_link_data(DG, nodes="nodes", edges="edges")

        # Ensure a graph exists for the user. Create if it doesn't exist.
        statement = select(CogGraph).where(CogGraph.owner_id == user1.id)
        graph1 = session.exec(statement).first()
        if not graph1:
            graph1 = CogGraph(model_name="test_model", graph_json=str(DG_data), owner_id=user1.id)
            session.add(graph1)
            session.commit()
            session.refresh(graph1)

    print("graph1:", graph1)
    return {"message": "Mock data created", "graph": graph1.graph_json}


# ----------------- Public (no auth) -----------------

# Create user (no auth)
@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(user_name: str, password: str):
    if not user_name.isalnum():
        raise HTTPException(status_code=400, detail="User name must be alphanumeric")
    hashed = get_password_hash(password)
    with Session(engine) as session:
        statement = select(User).where(User.user_name == user_name)
        user1 = session.exec(statement).first()
        if user1:
            raise HTTPException(status_code=400, detail="User already exists")
        user1 = User(user_name=user_name, password=hashed)
        session.add(user1)
        session.commit()
        session.refresh(user1)
    return {"message": "User created"}

@app.post("/login", response_model=TokenResponse)
async def login(user_name: str, password: str):
    with Session(engine) as session:
        statement = select(User).where(User.user_name == user_name)
        user1 = session.exec(statement).first()
        if not user1:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        if not verify_password(password, user1.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(subject=user1.user_name)
    return {"access_token": token, "token_type": "bearer"}


# ----------------- Protected (auth) -----------------

# [GET] Return owned CogGRaphs for the current user
@app.get("/graphs")
async def graphs(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id)
        graphs = session.exec(statement).all()
    return {"graphs": graphs}

# [GET] Return available modules
@app.get("/modules")
async def modules(current_user: User = Depends(get_current_user)):
    return {"modules": components.modules}

# [GET] Return user details
@app.get("/profile")
async def profile(current_user: User = Depends(get_current_user)):
    return {"user_name": current_user.user_name, "id": current_user.id}

# [GET] Return CogGraph "name" for the current user
@app.get("/load/{name}")
async def load_graph(name: str, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id, CogGraph.model_name == name)
        graph = session.exec(statement).first()
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return {"graph": graph.graph_json}

# [POST] Save posted GogGraph "name" for the current user
@app.post("/save/{name}")
async def save_graph(name: str, graph_json: str, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id, CogGraph.model_name == name)
        graph = session.exec(statement).first()
        if graph:
            graph.graph_json = graph_json
            session.add(graph)
            session.commit()
            session.refresh(graph)
        else:
            graph = CogGraph(model_name=name, graph_json=graph_json, owner_id=current_user.id)
            session.add(graph)
            session.commit()
            session.refresh(graph)
    return {"message": "Graph saved", "graph": graph.graph_json}

# [POST] Run CogGraph "name" with posted POV png
@app.post("/run/{name}")
async def run_graph(name: str, file: UploadFile, current_user: User = Depends(get_current_user)):
    # Save the file to disk and get the path
    save_result = save_obs_to_disk(file)
    if save_result != "ok":
        raise HTTPException(status_code=500, detail="Failed to save OBS")
    img_path = latest_obs_on_disk()

    # Load the graph from the database
    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id, CogGraph.model_name == name)
        graph = session.exec(statement).first()
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Run the graph with the img_path as input for the first module
    # For simplicity, we assume the first module is always "ItT" (image to text)
    result = await components.image_to_text(img_path)
    return {"result": result}
