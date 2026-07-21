# SQLmodel is used as ORM
from sqlmodel import Field, Session, SQLModel, Text

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_name: str = Field(index=True)
    password: str

class CogGraph(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    model_name: str = Field(index=True)
    # Store the graph as a JSON string
    graph_json: str = Field(default="{}", sa_column=Text)
    owner_id: int = Field(foreign_key="user.id")
