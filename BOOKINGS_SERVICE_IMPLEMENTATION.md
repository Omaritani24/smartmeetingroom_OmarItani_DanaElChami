# Bookings Service Implementation Summary

## Overview
This document summarizes the implementation of the Bookings microservice for the Smart Meeting Room project.

## What Was Implemented

### Bookings Service (`bookings_service/`)

#### 1. Database & Models
- **Database**: SQLite database (`bookings.db`)
- **Booking Model**: Includes fields for:
  - `id`: Primary key
  - `user_id`: Reference to users service (integer)
  - `room_id`: Reference to rooms service (integer)
  - `start_time`: Booking start datetime
  - `end_time`: Booking end datetime
  - `status`: Booking status (pending, confirmed, cancelled, completed)
  - `created_at`: Timestamp when booking was created
  - `updated_at`: Timestamp when booking was last updated
  - `notes`: Optional notes for the booking

#### 2. Authentication & Security
- **JWT Token Validation**: Validates tokens by calling the users service
- **Role-Based Access Control (RBAC)**:
  - **Regular Users**: Can create, view, update, and cancel their own bookings
  - **Admins**: Can view, update, and cancel any booking
  - **Facility Managers**: Can view all bookings (for planning purposes)

#### 3. API Endpoints

##### Core Booking Operations
- `POST /bookings` - Create a new booking
  - Validates room exists and is available
  - Checks for time slot conflicts
  - Prevents bookings in the past
  - Requires authentication

- `GET /bookings` - Get all bookings
  - Regular users: see only their own bookings
  - Admins/Facility Managers: see all bookings
  - Supports filtering by status, room_id, user_id
  - Supports pagination (skip, limit)

- `GET /bookings/{booking_id}` - Get specific booking by ID
  - Regular users: can only view their own bookings
  - Admins/Facility Managers: can view any booking

- `PUT /bookings/{booking_id}` - Update a booking
  - Can update room, time slot, status, notes
  - Validates conflicts when changing time/room
  - Regular users: can only update their own bookings
  - Admins/Facility Managers: can update any booking

- `DELETE /bookings/{booking_id}` - Cancel a booking (soft delete)
  - Sets status to "cancelled" instead of deleting
  - Regular users: can only cancel their own bookings
  - Admins/Facility Managers: can cancel any booking

##### Availability & History
- `GET /bookings/availability/check` - Check room availability
  - Takes room_id, start_time, end_time as query parameters
  - Returns availability status and conflicting bookings if any

- `GET /bookings/user/{user_id}/history` - Get user's booking history
  - Regular users: can only view their own history
  - Admins/Facility Managers: can view any user's history
  - Supports filtering by status
  - Supports pagination

- `GET /bookings/room/{room_id}` - Get all bookings for a room
  - All authenticated users can view room bookings
  - Supports date range filtering (start_date, end_date)
  - Supports pagination

##### Health & Status
- `GET /` - Root endpoint (service status)
- `GET /health` - Health check endpoint

#### 4. Features

##### Inter-Service Communication
- **Users Service Integration**: 
  - Validates JWT tokens by calling `/users/me` endpoint
  - Verifies user existence when needed
- **Rooms Service Integration**:
  - Verifies room existence before creating bookings
  - Checks room availability status
  - Gets room details for validation

##### Conflict Detection
- Checks for overlapping time slots when creating/updating bookings
- Prevents double-booking of rooms
- Returns detailed conflict information

##### Validation
- Validates that end_time is after start_time
- Prevents bookings in the past
- Validates room existence and availability
- Input sanitization to prevent SQL injection (using SQLAlchemy ORM)

##### Booking Status Management
- Supports status transitions: pending → confirmed → completed
- Soft delete via status change to "cancelled"
- Prevents updates to cancelled/completed bookings (unless admin)

#### 5. Error Handling
- Comprehensive error responses with appropriate HTTP status codes
- Clear error messages for validation failures
- Handles service unavailability gracefully

## File Structure

```
bookings_service/
├── __init__.py
├── app.py              # FastAPI application with all endpoints
├── models.py           # SQLAlchemy Booking model
├── schemas.py          # Pydantic schemas for request/response
├── database.py         # Database configuration
├── auth.py             # Authentication utilities (JWT validation via users service)
├── Dockerfile          # Container definition for bookings service
└── tests/
    ├── __init__.py
    └── test_bookings.py   # Unit tests
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

**Terminal 3 - Bookings Service:**
```bash
export USERS_SERVICE_URL=http://localhost:8000
export ROOMS_SERVICE_URL=http://localhost:8001
uvicorn bookings_service.app:app --port 8002 --reload
```

### Option 2: Use the Helper Script
```bash
python run_services.py
```

### Option 3: Docker Compose
```bash
docker compose up --build
```

This builds all three service images, exposes them on ports 8000/8001/8002, and uses named volumes to persist the SQLite files across restarts.

## Testing

### Manual Testing with test_services.py
```bash
# First, start all services (see above)
# Then run:
python test_services.py
```

### Unit Tests
```bash
cd bookings_service
pytest tests/test_bookings.py -v
```

### API Documentation
Once services are running, visit:
- Users Service: http://localhost:8000/docs
- Rooms Service: http://localhost:8001/docs
- Bookings Service: http://localhost:8002/docs

FastAPI automatically provides interactive API documentation (Swagger UI).

## Example API Calls

### Create a Booking
```bash
# First, login to get a token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepass123"
  }'

# Create a booking
curl -X POST "http://localhost:8002/bookings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "room_id": 1,
    "start_time": "2025-12-20T10:00:00",
    "end_time": "2025-12-20T12:00:00",
    "notes": "Team meeting"
  }'
```

### Get All Bookings
```bash
curl -X GET "http://localhost:8002/bookings" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Check Room Availability
```bash
curl -X GET "http://localhost:8002/bookings/availability/check?room_id=1&start_time=2025-12-20T10:00:00&end_time=2025-12-20T12:00:00" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Get User Booking History
```bash
curl -X GET "http://localhost:8002/bookings/user/1/history" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Update a Booking
```bash
curl -X PUT "http://localhost:8002/bookings/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "start_time": "2025-12-20T11:00:00",
    "end_time": "2025-12-20T13:00:00",
    "notes": "Updated meeting time"
  }'
```

### Cancel a Booking
```bash
curl -X DELETE "http://localhost:8002/bookings/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Role-Based Access Control (RBAC)

### Regular User
-  Create bookings for themselves
-  View their own bookings
-  Update their own bookings
-  Cancel their own bookings
-  View their own booking history
-  Check room availability
-  View other users' bookings
-  Cancel other users' bookings

### Admin
-  All regular user permissions
-  View all bookings
-  Update any booking
-  Cancel any booking
-  View any user's booking history
-  Override booking status restrictions

### Facility Manager
-  All regular user permissions
-  View all bookings (for planning)
-  View any user's booking history
-  Cannot update/cancel other users' bookings (unless they own them)

## Security Features

1. **Authentication**: All endpoints require valid JWT tokens
2. **Authorization**: Role-based access control enforced
3. **Input Validation**: Pydantic schemas validate all inputs
4. **SQL Injection Prevention**: Using SQLAlchemy ORM (parameterized queries)
5. **Conflict Prevention**: Prevents double-booking through time slot validation
6. **Service Isolation**: Each service has its own database

## Next Steps

1. **Environment Variables**: Move service URLs and configuration to environment variables
2. **Database Migration**: Consider using Alembic for database migrations
3. **Error Handling**: Add more comprehensive error handling and logging
4. **Caching**: Implement caching for frequently accessed data (room availability, user info)
5. **Notifications**: Add notification system for booking confirmations/cancellations
6. **Testing**: Expand test coverage with more edge cases and integration tests
7. **Documentation**: Generate Sphinx documentation
8. **Performance Profiling**: Add performance profiling and monitoring

## Notes

- The bookings service uses SQLite database for simplicity. For production, consider PostgreSQL or MySQL.
- Service URLs are configurable via environment variables for flexibility between local and Docker deployments.
- All endpoints include proper validation using Pydantic schemas.
- The service is designed to be independent but integrates with users and rooms services via HTTP calls.
- Booking conflicts are detected by checking overlapping time ranges in the database.

