# Users and Rooms Services Implementation Summary

## Overview
This document summarizes the implementation of the Users and Rooms microservices for the Smart Meeting Room project.

## What Was Implemented

### Users Service (`users_service/`)

#### 1. Database & Models
- **Database**: SQLite database (`users.db`)
- **User Model**: Includes fields for id, name, username, email, hashed_password, and role

#### 2. Authentication & Security
- **Password Hashing**: Using bcrypt via passlib
- **JWT Tokens**: Token-based authentication with configurable expiration
- **OAuth2**: Password bearer token flow

#### 3. API Endpoints
- `POST /register` - Register a new user
- `POST /login` - Login and get access token
- `GET /users/me` - Get current user information (requires authentication)
- `GET /users` - Get all users (admin only)
- `GET /users/{user_id}` - Get specific user by ID
- `GET /users/by-username/{username}` - Get user details by username
- `PUT /users/{user_id}` - Update user (users can update themselves, admins can update anyone)
- `DELETE /users/{user_id}` - Delete user (admin only)

#### 4. Features
- User registration with validation
- Secure password hashing
- JWT token generation and validation
- Role-based access control (regular users vs admin)
- Email and username uniqueness validation

### Rooms Service (`rooms_service/`)

#### 1. Database & Models
- **Database**: SQLite database (`rooms.db`)
- **Room Model**: Includes fields for id, name, description, capacity, location, amenities, price_per_hour, and is_available

#### 2. API Endpoints
- `POST /rooms` - Create a new room
- `GET /rooms` - Get all rooms (with optional filtering)
- `GET /rooms/{room_id}` - Get specific room by ID
- `PUT /rooms/{room_id}` - Update a room
- `DELETE /rooms/{room_id}` - Delete a room
- `GET /rooms/search/available` - Search available rooms with filters (capacity, price, location)

#### 3. Features
- Full CRUD operations for rooms
- Search functionality with multiple filters
- Availability filtering
- Capacity and price validation

## File Structure

```
smartmeetingroom_OmarItani_DanaElChami/
├── users_service/
│   ├── __init__.py
│   ├── app.py              # FastAPI application with all endpoints
│   ├── models.py           # SQLAlchemy User model
│   ├── schemas.py          # Pydantic schemas for request/response
│   ├── database.py         # Database configuration
│   ├── auth.py             # Authentication utilities (JWT, password hashing)
│   └── Dockerfile          # Container definition for users service
│   └── tests/
│       └── test_users.py   # Unit tests
├── rooms_service/
│   ├── __init__.py
│   ├── app.py              # FastAPI application with all endpoints
│   ├── models.py           # SQLAlchemy Room model
│   ├── schemas.py          # Pydantic schemas for request/response
│   ├── database.py         # Database configuration
│   └── Dockerfile          # Container definition for rooms service
│   └── tests/
│       └── test_rooms.py   # Unit tests
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Spins up both services
├── test_services.py        # Integration test script
└── run_services.py         # Script to run both services
```

## How to Run

### Option 1: Run Services Separately

**Terminal 1 - Users Service:**
```bash
uvicorn users_service.app:app --port 8000 --reload
```

**Terminal 2 - Rooms Service:**
```bash
uvicorn rooms_service.app:app --port 8001 --reload
```

### Option 2: Use the Helper Script
```bash
python run_services.py
```

### Option 3: Docker Compose
```bash
docker compose up --build
```

This builds both service images, exposes them on ports 8000/8001, and uses named volumes (`users_db`, `rooms_db`) to persist the SQLite files (`/app/users.db` and `/app/rooms.db`) across restarts. Stop with `Ctrl+C`, then `docker compose down` when finished.

## Testing

### Manual Testing with test_services.py
```bash
# First, start both services (see above)
# Then run:
python test_services.py
```

### API Documentation
Once services are running, visit:
- Users Service: http://localhost:8000/docs
- Rooms Service: http://localhost:8001/docs

FastAPI automatically provides interactive API documentation (Swagger UI).

## Example API Calls

### Users Service

**Register a user:**
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123",
    "role": "regular"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepass123"
  }'
```

**Get current user (requires token):**
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Rooms Service

**Create a room:**
```bash
curl -X POST "http://localhost:8001/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conference Room A",
    "description": "Large conference room",
    "capacity": 20,
    "location": "Building 1, Floor 2",
    "amenities": "Projector, Whiteboard, WiFi",
    "price_per_hour": 50.0,
    "is_available": true
  }'
```

**Get all rooms:**
```bash
curl -X GET "http://localhost:8001/rooms"
```

**Search available rooms:**
```bash
curl -X GET "http://localhost:8001/rooms/search/available?min_capacity=10&max_price=100"
```

## Next Steps

1. **Environment Variables**: Move sensitive configuration (like SECRET_KEY) to environment variables
2. **Database Migration**: Consider using Alembic for database migrations
3. **Error Handling**: Add more comprehensive error handling and logging
4. **Authentication for Rooms**: Add authentication/authorization to rooms endpoints if needed
5. **Integration**: Connect rooms service with bookings service
6. **Testing**: Expand test coverage with more edge cases
7. **Docker**: Containerize the services using Docker

## Notes

- Both services use SQLite databases for simplicity. For production, consider PostgreSQL or MySQL.
- The SECRET_KEY in `users_service/auth.py` should be changed to a secure random string in production.
- All endpoints include proper validation using Pydantic schemas.
- The services are designed to be independent and can be deployed separately.

