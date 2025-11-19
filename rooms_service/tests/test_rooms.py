import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rooms_service.app import app, get_db
from rooms_service.database import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rooms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "rooms", "status": "running"}


def test_create_room():
    """Test room creation."""
    room_data = {
        "name": "Conference Room A",
        "description": "A large conference room",
        "capacity": 20,
        "location": "Building 1, Floor 2",
        "amenities": "Projector, Whiteboard, WiFi",
        "price_per_hour": 50.0,
        "is_available": True
    }
    response = client.post("/rooms", json=room_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Conference Room A"
    assert data["capacity"] == 20
    assert "id" in data


def test_get_rooms():
    """Test getting all rooms."""
    response = client.get("/rooms")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_room_by_id():
    """Test getting a room by ID."""
    # First create a room
    room_data = {
        "name": "Test Room",
        "capacity": 10,
        "is_available": True
    }
    create_response = client.post("/rooms", json=room_data)
    room_id = create_response.json()["id"]
    
    # Get the room
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Test Room"


def test_get_nonexistent_room():
    """Test getting a room that doesn't exist."""
    response = client.get("/rooms/99999")
    assert response.status_code == 404


def test_update_room():
    """Test updating a room."""
    # Create a room
    room_data = {
        "name": "Original Room",
        "capacity": 5,
        "is_available": True
    }
    create_response = client.post("/rooms", json=room_data)
    room_id = create_response.json()["id"]
    
    # Update the room
    update_data = {
        "name": "Updated Room",
        "capacity": 15
    }
    response = client.put(f"/rooms/{room_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Room"
    assert data["capacity"] == 15


def test_delete_room():
    """Test deleting a room."""
    # Create a room
    room_data = {
        "name": "Room to Delete",
        "capacity": 5,
        "is_available": True
    }
    create_response = client.post("/rooms", json=room_data)
    room_id = create_response.json()["id"]
    
    # Delete the room
    response = client.delete(f"/rooms/{room_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404


def test_update_room_status():
    """Test updating room availability status."""
    # Create a room
    room_data = {
        "name": "Status Room",
        "capacity": 8,
        "is_available": True
    }
    create_response = client.post("/rooms", json=room_data)
    room_id = create_response.json()["id"]

    # Update status to False
    status_response = client.patch(f"/rooms/{room_id}/status", json={"is_available": False})
    assert status_response.status_code == 200
    assert status_response.json()["is_available"] is False

    # Verify regular GET reflects change
    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_available"] is False


def test_search_available_rooms():
    """Test searching for available rooms."""
    response = client.get("/rooms/search/available")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All returned rooms should be available
    for room in data:
        assert room["is_available"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

