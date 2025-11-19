from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import Base, engine, SessionLocal
from . import models, schemas

app = FastAPI(title="Rooms Service")
# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"service": "rooms", "status": "running"}

@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "up"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


@app.post("/rooms", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    """Create a new room."""
    db_room = models.Room(
        name=room.name,
        description=room.description,
        capacity=room.capacity,
        location=room.location,
        amenities=room.amenities,
        price_per_hour=room.price_per_hour,
        is_available=room.is_available
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@app.get("/rooms", response_model=List[schemas.RoomResponse])
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    available_only: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all rooms with optional filtering."""
    query = db.query(models.Room)
    
    if available_only:
        query = query.filter(models.Room.is_available == True)
    
    rooms = query.offset(skip).limit(limit).all()
    return rooms


@app.get("/rooms/{room_id}", response_model=schemas.RoomResponse)
def read_room(room_id: int, db: Session = Depends(get_db)):
    """Get a specific room by ID."""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return db_room


@app.put("/rooms/{room_id}", response_model=schemas.RoomResponse)
def update_room(
    room_id: int,
    room_update: schemas.RoomUpdate,
    db: Session = Depends(get_db)
):
    """Update a room."""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Update fields
    update_data = room_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_room, field, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room


@app.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    """Delete a room."""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    db.delete(db_room)
    db.commit()
    return None


@app.patch("/rooms/{room_id}/status", response_model=schemas.RoomResponse)
def update_room_status(
    room_id: int,
    status_update: schemas.RoomStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update room availability status (used by booking service)."""
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    db_room.is_available = status_update.is_available
    db.commit()
    db.refresh(db_room)
    return db_room


@app.get("/rooms/search/available", response_model=List[schemas.RoomResponse])
def search_available_rooms(
    min_capacity: Optional[int] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Search for available rooms with filters."""
    query = db.query(models.Room).filter(models.Room.is_available == True)
    
    if min_capacity:
        query = query.filter(models.Room.capacity >= min_capacity)
    
    if max_price:
        query = query.filter(
            (models.Room.price_per_hour <= max_price) | (models.Room.price_per_hour.is_(None))
        )
    
    if location:
        query = query.filter(models.Room.location.ilike(f"%{location}%"))
    
    rooms = query.offset(skip).limit(limit).all()
    return rooms
