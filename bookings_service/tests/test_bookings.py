import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bookings_service.app import app, get_db
from bookings_service.database import Base
from bookings_service import auth, models
import bookings_service.app as bookings_app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bookings.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_current_user():
    return {"id": 1, "username": "testuser", "email": "test@example.com", "role": "regular"}

def override_admin():
    return {"id": 2, "username": "admin", "email": "admin@example.com", "role": "admin"}

def override_facility():
    return {"id": 3, "username": "facility", "email": "facility@example.com", "role": "facility_manager"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[auth.get_current_user] = override_current_user
app.dependency_overrides[auth.get_current_admin] = override_admin
app.dependency_overrides[auth.get_current_facility] = override_facility

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture
def mock_room_ok(monkeypatch):
    async def room_exists(room_id: int):
        return True
    async def room_available(room_id: int):
        return True
    monkeypatch.setattr(bookings_app, "room_exists", room_exists)
    monkeypatch.setattr(bookings_app, "room_available", room_available)

@pytest.fixture
def mock_room_missing(monkeypatch):
    async def room_exists(room_id: int):
        return False
    async def room_available(room_id: int):
        return True
    monkeypatch.setattr(bookings_app, "room_exists", room_exists)
    monkeypatch.setattr(bookings_app, "room_available", room_available)

@pytest.fixture
def mock_room_unavailable(monkeypatch):
    async def room_exists(room_id: int):
        return True
    async def room_available(room_id: int):
        return False
    monkeypatch.setattr(bookings_app, "room_exists", room_exists)
    monkeypatch.setattr(bookings_app, "room_available", room_available)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"service": "bookings", "status": "running"}

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_create_booking_success(mock_room_ok):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "notes": "Test booking"
    }
    r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    assert r.status_code == 201
    body = r.json()
    assert body["room_id"] == 1
    assert body["user_id"] == 1
    assert body["status"] == "confirmed"
    assert "id" in body

def test_create_booking_past_time(mock_room_ok):
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    assert r.status_code == 400

def test_create_booking_room_not_found(mock_room_missing):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 999,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    assert r.status_code == 404

def test_create_booking_room_unavailable(mock_room_unavailable):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    assert r.status_code == 400

def test_get_all_bookings(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    r = client.get("/bookings", headers={"Authorization": "Bearer token"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0

def test_get_booking_by_id(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    create_r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    booking_id = create_r.json()["id"]
    r = client.get(f"/bookings/{booking_id}", headers={"Authorization": "Bearer token"})
    assert r.status_code == 200
    assert r.json()["id"] == booking_id

def test_get_nonexistent_booking():
    r = client.get("/bookings/99999", headers={"Authorization": "Bearer token"})
    assert r.status_code == 404

def test_update_booking(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    create_r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    booking_id = create_r.json()["id"]
    new_start = start_time + timedelta(hours=1)
    new_end = new_start + timedelta(hours=2)
    update_data = {
        "start_time": new_start.isoformat(),
        "end_time": new_end.isoformat(),
        "notes": "Updated"
    }
    r = client.put(f"/bookings/{booking_id}", json=update_data, headers={"Authorization": "Bearer token"})
    assert r.status_code == 200
    assert r.json()["notes"] == "Updated"

def test_cancel_booking(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    create_r = client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    booking_id = create_r.json()["id"]
    r = client.delete(f"/bookings/{booking_id}", headers={"Authorization": "Bearer token"})
    assert r.status_code == 204
    get_r = client.get(f"/bookings/{booking_id}", headers={"Authorization": "Bearer token"})
    assert get_r.status_code == 200
    assert get_r.json()["status"] == "cancelled"

def test_check_availability_free(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    r = client.get(
        "/bookings/availability/check",
        params={
            "room_id": 1,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": "Bearer token"}
    )
    assert r.status_code == 200
    assert r.json()["is_available"] is True

def test_check_availability_conflict(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    r = client.get(
        "/bookings/availability/check",
        params={
            "room_id": 1,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": "Bearer token"}
    )
    assert r.status_code == 200
    assert r.json()["is_available"] is False

def test_user_booking_history(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    r = client.get("/bookings/user/1", headers={"Authorization": "Bearer token"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0

def test_room_bookings(mock_room_ok):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)
    data = {
        "room_id": 1,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    client.post("/bookings", json=data, headers={"Authorization": "Bearer token"})
    r = client.get("/bookings/room/1", headers={"Authorization": "Bearer token"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
