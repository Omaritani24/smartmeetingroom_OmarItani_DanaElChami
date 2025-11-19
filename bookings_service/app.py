from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, text
from datetime import datetime
import httpx
import os

from .database import Base, engine, SessionLocal
from . import models, schemas
from .auth import get_current_user, get_current_admin, get_current_facility

app = FastAPI()

Base.metadata.create_all(bind=engine)

USERS_URL = os.getenv("USERS_SERVICE_URL", "http://users_service:8000")
ROOMS_URL = os.getenv("ROOMS_SERVICE_URL", "http://rooms_service:8001")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def room_exists(room_id: int):
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{ROOMS_URL}/rooms/{room_id}", timeout=5)
            return r.status_code == 200
    except:
        return False

async def room_available(room_id: int):
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{ROOMS_URL}/rooms/{room_id}", timeout=5)
            if r.status_code == 200:
                return r.json().get("is_available", False)
    except:
        pass
    return False



def conflicts(db, room_id, start, end, exclude=None):
    q = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        or_(
            and_(models.Booking.start_time <= start, models.Booking.end_time > start),
            and_(models.Booking.start_time < end, models.Booking.end_time >= end),
            and_(models.Booking.start_time >= start, models.Booking.end_time <= end),
            and_(models.Booking.start_time <= start, models.Booking.end_time >= end)
        )
    )
    if exclude:
        q = q.filter(models.Booking.id != exclude)
    return q.all()

@app.get("/")
def root():
    return {"service": "bookings", "status": "running"}


@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except:
        raise HTTPException(status_code=503)


@app.get("/bookings", response_model=list[schemas.BookingResponse])
def all_bookings(
    db: Session = Depends(get_db),
    current = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    q = db.query(models.Booking)
    if current["role"] not in ["admin", "facility_manager"]:
        q = q.filter(models.Booking.user_id == current["id"])
    return q.order_by(models.Booking.start_time.desc()).offset(skip).limit(limit).all()


@app.get("/bookings/{booking_id}", response_model=schemas.BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    b = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404)
    if current["role"] not in ["admin", "facility_manager"] and b.user_id != current["id"]:
        raise HTTPException(status_code=403)
    return b


@app.post("/bookings", response_model=schemas.BookingResponse, status_code=201)
async def create_booking(
    data: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    if data.start_time < datetime.utcnow():
        raise HTTPException(status_code=400)
    if not await room_exists(data.room_id):
        raise HTTPException(status_code=404)
    if not await room_available(data.room_id):
        raise HTTPException(status_code=400)
    if conflicts(db, data.room_id, data.start_time, data.end_time):
        raise HTTPException(status_code=409)
    b = models.Booking(
        user_id=current["id"],
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time,
        notes=data.notes
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@app.put("/bookings/{booking_id}", response_model=schemas.BookingResponse)
async def update_booking(
    booking_id: int,
    data: schemas.BookingUpdate,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    b = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404)

    if current["role"] not in ["admin", "facility_manager"] and b.user_id != current["id"]:
        raise HTTPException(status_code=403)

    update = data.model_dump(exclude_unset=True)

    start = update.get("start_time", b.start_time)
    end = update.get("end_time", b.end_time)
    room = update.get("room_id", b.room_id)

    if end <= start:
        raise HTTPException(status_code=400)

    if "room_id" in update:
        if not await room_exists(room) or not await room_available(room):
            raise HTTPException(status_code=400)

    if conflicts(db, room, start, end, exclude=booking_id):
        raise HTTPException(status_code=409)

    for k, v in update.items():
        setattr(b, k, v)
    b.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(b)
    return b


@app.delete("/bookings/{booking_id}", status_code=204)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    b = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404)
    if current["role"] not in ["admin", "facility_manager"] and b.user_id != current["id"]:
        raise HTTPException(status_code=403)
    b.status = "cancelled"
    b.updated_at = datetime.utcnow()
    db.commit()
    return None



@app.get("/bookings/availability/check", response_model=schemas.AvailabilityResponse)
async def check_availability(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    if not await room_exists(room_id):
        raise HTTPException(status_code=404)
    if not await room_available(room_id):
        return schemas.AvailabilityResponse(is_available=False)
    c = conflicts(db, room_id, start_time, end_time)
    if c:
        return schemas.AvailabilityResponse(
            is_available=False,
            conflicting_bookings=[schemas.BookingResponse.model_validate(i) for i in c]
        )
    return schemas.AvailabilityResponse(is_available=True)


@app.get("/bookings/user/{user_id}", response_model=list[schemas.BookingResponse])
def user_history(
    user_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    if current["role"] not in ["admin", "facility_manager"] and current["id"] != user_id:
        raise HTTPException(status_code=403)
    return (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id)
        .order_by(models.Booking.start_time.desc())
        .all()
    )


@app.get("/bookings/room/{room_id}", response_model=list[schemas.BookingResponse])
def room_bookings(
    room_id: int,
    db: Session = Depends(get_db),
    current = Depends(get_current_user)
):
    return (
        db.query(models.Booking)
        .filter(models.Booking.room_id == room_id)
        .order_by(models.Booking.start_time.asc())
        .all()
    )
