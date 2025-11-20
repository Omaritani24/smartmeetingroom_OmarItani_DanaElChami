from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import httpx

from .database import Base, engine, SessionLocal
from . import models, schemas
from .auth import (
    get_password_hash,
    verify_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_user_by_username
)

app = FastAPI(title="Users Service")
Base.metadata.create_all(bind=engine)

BOOKINGS_SERVICE_URL = os.getenv("BOOKINGS_SERVICE_URL", "http://bookings_service:8002")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fetch_user_bookings(user_id: int):
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"{BOOKINGS_SERVICE_URL}/bookings/user/{user_id}")
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return []


@app.get("/")
def root():
    return {"service": "users", "status": "running"}


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


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
    {
        "sub": user.username,
        "id": user.id,
        "role": user.role
    }
)

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserWithBookings)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    user_data = schemas.UserResponse.model_validate(current_user).model_dump()
    user_data["bookings"] = fetch_user_bookings(current_user.id)
    return user_data


@app.get("/users", response_model=list[schemas.UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@app.get("/users/{user_id}/with-bookings", response_model=schemas.UserWithBookings)
def read_user_with_bookings(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user_data = schemas.UserResponse.model_validate(db_user).model_dump()
    user_data["bookings"] = fetch_user_bookings(user_id)
    return user_data


@app.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    if "username" in update_data and update_data["username"] != db_user.username:
        existing_user = get_user_by_username(db, username=update_data["username"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    if "email" in update_data and update_data["email"] != db_user.email:
        existing_user = db.query(models.User).filter(models.User.email == update_data["email"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    db.delete(db_user)
    db.commit()
    return None


@app.get("/users/by-username/{username}", response_model=schemas.UserResponse)
def read_user_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_user = get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.username != username and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return db_user


@app.post("/users/{user_id}/reset-password", response_model=schemas.UserResponse)
def reset_password(
    user_id: int,
    payload: schemas.PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.role != "admin":
        if payload.old_password is None or not verify_password(payload.old_password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Old password is incorrect"
            )
    db_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(db_user)
    return db_user
