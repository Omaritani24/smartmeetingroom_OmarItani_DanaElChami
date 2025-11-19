from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional

class BookingBase(BaseModel):
    room_id: int = Field(..., gt=0)
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_time(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return self

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    room_id: Optional[int] = Field(None, gt=0)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def check_time(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("End time must be after start time")
        return self

class BookingResponse(BookingBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_bookings: Optional[list[BookingResponse]] = None
