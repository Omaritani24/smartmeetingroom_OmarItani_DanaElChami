from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from .database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=True)
    amenities = Column(Text, nullable=True)  # JSON string or comma-separated
    price_per_hour = Column(Float, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)

