from fastapi import FastAPI

app = FastAPI(title="Users Service")

@app.get("/")
def root():
    return {"service": "users", "status": "running"}

@app.get("/health")
def health():
    # we'll later make this check the DB; for now it's a stub
    return {"status": "ok"}
