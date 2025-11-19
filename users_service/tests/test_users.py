import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from users_service.app import app, get_db
from users_service.database import Base
from users_service import auth

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_users.db"
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

# Reset tables before running tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
auth.SessionLocal = TestingSessionLocal

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "users", "status": "running"}


def test_register_user():
    """Test user registration."""
    user_data = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "regular"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_username():
    """Test registration with duplicate username."""
    user_data = {
        "name": "Test User 2",
        "username": "testuser",
        "email": "test2@example.com",
        "password": "testpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 400


def test_login():
    """Test user login."""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    """Test login with wrong password."""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user():
    """Test getting current user info."""
    # First login to get token
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    login_response = client.post("/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_get_user_by_username_endpoint():
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    login_response = client.post("/login", json=login_data)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/by-username/testuser", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


def test_password_reset_self():
    # login to get token
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # reset password
    reset_payload = {"old_password": "testpass123", "new_password": "newpass456"}
    response = client.post("/users/1/reset-password", json=reset_payload, headers=headers)
    assert response.status_code == 200

    # login with new password succeeds
    new_login = client.post("/login", json={"username": "testuser", "password": "newpass456"})
    assert new_login.status_code == 200

    # old password fails
    old_login = client.post("/login", json={"username": "testuser", "password": "testpass123"})
    assert old_login.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

