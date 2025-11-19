from pydantic import BaseModel, Field
from typing import Optional


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: int = Field(gt=0, description="Room capacity must be greater than 0")
    location: Optional[str] = None
    amenities: Optional[str] = None
    price_per_hour: Optional[float] = Field(None, ge=0, description="Price must be non-negative")
    is_available: bool = True


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0)
    location: Optional[str] = None
    amenities: Optional[str] = None
    price_per_hour: Optional[float] = Field(None, ge=0)
    is_available: Optional[bool] = None


class RoomResponse(RoomBase):
    id: int

    class Config:
        from_attributes = True


class RoomStatusUpdate(BaseModel):
    is_available: bool

