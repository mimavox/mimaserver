from fastapi import FastAPI, UploadFile, HTTPException, Depends, status
import glob
import os

import time
import json
import networkx as nx
from typing import Dict, Any
from pydantic import BaseModel
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from session.auth import get_password_hash, verify_password, create_access_token, get_current_user
import cog_graphs.components as components

# Database connection
from database.connect import create_engine
from database.connect import clear_db_and_tables
from database.models import CogGraph, User

# ----------------- Pydantic Models -----------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    user_name: str
    password: str

class UserLogin(BaseModel):
    user_name: str
    password: str

class GraphSavePayload(BaseModel):
    # Accept a standard JSON object instead of a string
    graph_json: Dict[str, Any]

# ---------------------------------------------------


# DATABASE_URL is set as env variable in fastapi cloud
engine = create_engine(os.getenv("DATABASE_URL"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic goes here
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

def get_graph(name: str, current_user: User):
    """Helper: fetch a CogGraph record owned by `current_user` with the given `name`.

    Returns a tuple (graph_record, parsed_graph_dict).
    Raises HTTPException(404) if not found, HTTPException(500) if the stored JSON can't be parsed.
    """
    owner_id = current_user.id
    if owner_id is None:
        # This should not happen for a properly authenticated user
        raise HTTPException(status_code=500, detail="Authenticated user has no id")

    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == owner_id, CogGraph.model_name == name)
        graph_record = session.exec(statement).first()
    if not graph_record:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Try to parse the stored graph JSON. Fallback to ast.literal_eval for Python reprs.
    try:
        parsed = json.loads(graph_record.graph_json)
    except (TypeError, json.JSONDecodeError):
        import ast
        try:
            parsed = ast.literal_eval(graph_record.graph_json)
        except Exception:
            raise HTTPException(status_code=500, detail="Stored graph is not valid JSON")

    return graph_record, parsed


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
            assert user1.id is not None
            graph1 = CogGraph(model_name="test_model", graph_json=str(DG_data), owner_id=user1.id)
            session.add(graph1)
            session.commit()
            session.refresh(graph1)

    print("graph1:", graph1)
    return {"message": "Mock data created", "graph": graph1.graph_json}


# ----------------- Public (no auth) -----------------

# Create user (no auth)
@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    if not payload.user_name.isalnum():
        raise HTTPException(status_code=400, detail="User name must be alphanumeric")
    hashed = get_password_hash(payload.password)
    with Session(engine) as session:
        statement = select(User).where(User.user_name == payload.user_name)
        user1 = session.exec(statement).first()
        if user1:
            raise HTTPException(status_code=400, detail="User already exists")
        user1 = User(user_name=payload.user_name, password=hashed)
        session.add(user1)
        session.commit()
        session.refresh(user1)
    return {"message": "User created"}

@app.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    with Session(engine) as session:
        statement = select(User).where(User.user_name == payload.user_name)
        user1 = session.exec(statement).first()
        if not user1:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        if not verify_password(payload.password, user1.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(subject=user1.user_name)
    return {"access_token": token, "token_type": "bearer"}


# ----------------- Protected (auth) -----------------

# [GET] Return owned CogGraphs for the current user TODO: Test format of returned graphs
@app.get("/graphs")
async def get_all_graphs(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id)
        graphs = session.exec(statement).all()
    return {"graphs": graphs}

# [GET] Return available modules TODO: Change to everyone can alway reach all modules
@app.get("/modules")
async def modules(current_user: User = Depends(get_current_user)):
    return {"modules": components.modules}

# [GET] Return user details TODO: Add fields for personal data in model
@app.get("/profile")
async def profile(current_user: User = Depends(get_current_user)):
    return {"user_name": current_user.user_name, "id": current_user.id}

# [GET] Return CogGraph "name" for the current user
@app.get("/load/{name}")
async def load_graph(name: str, current_user: User = Depends(get_current_user)):
    # Reuse helper to fetch the record. Keep returning the raw stored JSON string for backward compatibility.
    graph_record, _ = get_graph(name, current_user)
    return {"graph": graph_record.graph_json}

# [POST] Save posted GogGraph "name" for the current user (assume correct incoming format)
@app.post("/save/{name}")
async def save_graph(name: str, payload: GraphSavePayload, current_user: User = Depends(get_current_user)):
    # Convert the clean dictionary into a string for the database
    json_string = json.dumps(payload.graph_json)

    with Session(engine) as session:
        statement = select(CogGraph).where(CogGraph.owner_id == current_user.id, CogGraph.model_name == name)
        graph = session.exec(statement).first()
        if graph:
            graph.graph_json = json_string
            session.add(graph)
            session.commit()
            session.refresh(graph)
        else:
            assert current_user.id is not None
            graph = CogGraph(model_name=name, graph_json=json_string, owner_id=current_user.id)
            session.add(graph)
            session.commit()
            session.refresh(graph)
    return {"message": "Graph saved", "graph": graph.graph_json}

# [POST] Run CogGraph "name" with posted POV png
# TODO: Build networkx graph from stored graph-json format.
# TODO: Run the constructed networkx graph.
@app.post("/run/{name}")
async def run_graph(name: str, file: UploadFile, current_user: User = Depends(get_current_user)):
    # Save incoming png to disk and get save path
    save_result = save_obs_to_disk(file)
    if save_result != "ok":
        raise HTTPException(status_code=500, detail="Failed to save OBS")
    img_path = latest_obs_on_disk()

    # Fetch the record and parsed graph using the helper
    graph_record, graph = get_graph(name, current_user)



    """
    node_count = len(graph.get("nodes") or [])
    edge_count = len(graph.get("edges") or [])
    print(f"Loaded graph '{name}' for user {current_user.user_name}: nodes={node_count}, edges={edge_count}")

    # Run the graph with the img_path as input for the first module
    # For simplicity, we assume the first module is always "ItT" (image to text)
    result = await components.image_to_text(img_path)
    """
    return {"result": ""}
