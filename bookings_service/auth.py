from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://127.0.0.1:8001/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user = {
            "id": payload.get("id"),
            "username": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }

        if user["username"] is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception
