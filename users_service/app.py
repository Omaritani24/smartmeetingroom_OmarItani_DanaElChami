from fastapi import FastAPI

app = FastAPI(title="Rooms Service")

@app.get("/")
def root():
    return {"service": "rooms", "status": "running"}

@app.get("/health")
def health():
    # will become a real DB health check later
    return {"status": "ok"}
