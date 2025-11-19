"""
Script to run both services for testing.
"""
import subprocess
import sys
import os

def run_services():
    """Run users, rooms, and bookings services."""
    print("Starting services...")
    print("Users service will run on http://localhost:8000")
    print("Rooms service will run on http://localhost:8001")
    print("Bookings service will run on http://localhost:8002")
    print("\nPress Ctrl+C to stop all services\n")
    
    # Set environment variables for local development
    os.environ["USERS_SERVICE_URL"] = "http://localhost:8000"
    os.environ["ROOMS_SERVICE_URL"] = "http://localhost:8001"
    
    try:
        # Start users service
        users_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "users_service.app:app", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Start rooms service
        rooms_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "rooms_service.app:app", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Start bookings service
        bookings_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "bookings_service.app:app", "--port", "8002"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Services started!")
        print("Users service PID:", users_process.pid)
        print("Rooms service PID:", rooms_process.pid)
        print("Bookings service PID:", bookings_process.pid)
        
        # Wait for all processes
        users_process.wait()
        rooms_process.wait()
        bookings_process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping services...")
        users_process.terminate()
        rooms_process.terminate()
        bookings_process.terminate()
        print("Services stopped.")

if __name__ == "__main__":
    run_services()

