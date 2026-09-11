import uuid
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

# Base properties shared across schemas
class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=100)


# Schema for incoming registration request (requires plain password)
class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)


# Schema for API response (EXCLUDES password entirely)
class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    # Tells Pydantic to read ORM models directly
    model_config = {
        "from_attributes": True
    }