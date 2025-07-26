from pydantic import BaseModel

class Actions(BaseModel):
    left: bool
    right: bool
    forward: bool
    backward: bool
    jump: bool
