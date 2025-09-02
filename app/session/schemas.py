from pydantic import BaseModel

class UserCreate(BaseModel):
    user_name: str
    password: str

class LoginRequest(BaseModel):
    user_name: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"