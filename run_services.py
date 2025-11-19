"""
Script to run both services for testing.
"""
import subprocess
import sys
import os

def run_services():
    """Run both users and rooms services."""
    print("Starting services...")
    print("Users service will run on http://localhost:8000")
    print("Rooms service will run on http://localhost:8001")
    print("\nPress Ctrl+C to stop all services\n")
    
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
        
        print("Services started!")
        print("Users service PID:", users_process.pid)
        print("Rooms service PID:", rooms_process.pid)
        
        # Wait for both processes
        users_process.wait()
        rooms_process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping services...")
        users_process.terminate()
        rooms_process.terminate()
        print("Services stopped.")

if __name__ == "__main__":
    run_services()

