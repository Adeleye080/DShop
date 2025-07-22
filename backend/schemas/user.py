from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field("", max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserProfile(BaseModel):
    full_name: str = Field(..., max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    preferences: Optional[dict] = {}


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[datetime] = None
    preferences: Optional[dict] = None


class UserProfileOut(UserProfile):
    id: int
    email: EmailStr
    is_active: bool
    email_verified: bool
    created_at: datetime
    role: str

    class Config:
        from_attributes = True
