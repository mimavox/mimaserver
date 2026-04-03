from fastapi import FastAPI, UploadFile, HTTPException, Depends, status
from sqlmodel import Field, Session, SQLModel, Text, create_engine, select

import glob
import os
import time

import networkx as nx


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    password: str

class CogGraph(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    model_name: str = Field(index=True)
    graph_json: str = Field(default="{}", sa_column=Text)  # Store the graph as a JSON string
    owner_id: int = Field(foreign_key="user.id")


engine = create_engine(os.getenv("DATABASE_URL"))

def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
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
        
        DG = nx.DiGraph()
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

    
    
