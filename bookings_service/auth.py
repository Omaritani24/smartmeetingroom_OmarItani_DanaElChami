import httpx
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import os

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users_service:8000")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def verify_token(token: str):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{USERS_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if r.status_code == 200:
                return r.json()
    except:
        pass
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = await verify_token(token)
    if user is None:
        raise HTTPException(status_code=401)
    return user

async def get_current_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403)
    return user

async def get_current_facility(user=Depends(get_current_user)):
    if user.get("role") not in ["facility_manager", "admin"]:
        raise HTTPException(status_code=403)
    return user
