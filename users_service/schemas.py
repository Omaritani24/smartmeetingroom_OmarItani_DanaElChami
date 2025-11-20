from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str
    username: str
    email: EmailStr
    role: str = "regular"


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    old_password: Optional[str] = Field(None, min_length=6)
    new_password: str = Field(..., min_length=6)


class UserWithBookings(UserResponse):
    bookings: list[dict] = []
