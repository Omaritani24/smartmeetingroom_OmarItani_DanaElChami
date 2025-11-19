"""
Simple test script to verify users and rooms services are working.
Run this from the project root directory.
"""
import sys
import requests
import time
import subprocess
import os

def test_users_service():
    """Test users service endpoints."""
    print("\n" + "="*50)
    print("Testing Users Service")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False
    
    # Test register
    try:
        user_data = {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "role": "regular"
        }
        response = requests.post(f"{base_url}/register", json=user_data)
        print(f"✓ Register: {response.status_code}")
        if response.status_code == 201:
            user = response.json()
            print(f"  Created user: {user['username']} (ID: {user['id']})")
    except Exception as e:
        print(f"✗ Register failed: {e}")
        return False
    
    # Test login
    try:
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        response = requests.post(f"{base_url}/login", json=login_data)
        print(f"✓ Login: {response.status_code}")
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"  Got access token: {token[:20]}...")
            return token
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return False
    
    return None


def test_rooms_service():
    """Test rooms service endpoints."""
    print("\n" + "="*50)
    print("Testing Rooms Service")
    print("="*50)
    
    base_url = "http://localhost:8001"
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"✓ Root endpoint: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
        return False
    
    # Test create room
    try:
        room_data = {
            "name": "Conference Room A",
            "description": "A large conference room",
            "capacity": 20,
            "location": "Building 1, Floor 2",
            "amenities": "Projector, Whiteboard, WiFi",
            "price_per_hour": 50.0,
            "is_available": True
        }
        response = requests.post(f"{base_url}/rooms", json=room_data)
        print(f"✓ Create room: {response.status_code}")
        if response.status_code == 201:
            room = response.json()
            print(f"  Created room: {room['name']} (ID: {room['id']})")
            return room['id']
    except Exception as e:
        print(f"✗ Create room failed: {e}")
        return False
    
    # Test get rooms
    try:
        response = requests.get(f"{base_url}/rooms")
        print(f"✓ Get rooms: {response.status_code}")
        if response.status_code == 200:
            rooms = response.json()
            print(f"  Found {len(rooms)} rooms")
    except Exception as e:
        print(f"✗ Get rooms failed: {e}")
        return False
    
    return None


if __name__ == "__main__":
    print("\n" + "="*50)
    print("Service Testing Script")
    print("="*50)
    print("\nNote: Make sure both services are running:")
    print("  - Users service: uvicorn users_service.app:app --port 8000")
    print("  - Rooms service: uvicorn rooms_service.app:app --port 8001")
    print("\nWaiting 2 seconds for services to be ready...")
    time.sleep(2)
    
    # Test services
    users_token = test_users_service()
    rooms_id = test_rooms_service()
    
    print("\n" + "="*50)
    print("Testing Complete!")
    print("="*50)
    if users_token:
        print("✓ Users service is working")
    else:
        print("✗ Users service has issues")
    
    if rooms_id:
        print("✓ Rooms service is working")
    else:
        print("✗ Rooms service has issues")

