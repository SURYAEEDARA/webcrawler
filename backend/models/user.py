from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    email: str
    username: str
    password: str

class UserRead(SQLModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

class UserLogin(SQLModel):
    email: str
    password: str

class Token(SQLModel):
    access_token: str
    token_type: str