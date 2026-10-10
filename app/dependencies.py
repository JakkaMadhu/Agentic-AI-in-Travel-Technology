from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.database import db
from app.models.user import User
from app.core.security import decode_token

security_scheme = HTTPBearer(auto_error=True)

def get_db() -> Generator:
    """Dependency ensuring safe Peewee connection open/close per request."""
    if db.is_closed():
        db.connect()
    try:
        yield db
    finally:
        if not db.is_closed():
            db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    _db: Generator = Depends(get_db)
) -> User:
    """Authenticate request using Bearer JWT access token and return User model."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = User.get_or_none(User.id == int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
