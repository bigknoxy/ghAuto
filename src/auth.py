"""Authentication module for ghAuto."""
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("GHAUTO_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return username


class AuthManager:
    """Manages authentication for ghAuto."""
    
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path  # If None, get_session() will use default ~/.ghauto/data/ghauto.db
    
    def authenticate_admin(self, password: str) -> bool:
        """Authenticate admin password."""
        # In production, store hashed password in database
        stored_hash = self._get_admin_password_hash()
        return stored_hash and verify_password(password, stored_hash)
    
    def set_admin_password(self, password: str):
        """Set admin password."""
        from db import get_session, Config
        session = get_session(self.db_path)
        
        config = session.query(Config).filter_by(key="admin_password_hash").first()
        if not config:
            config = Config(key="admin_password_hash", value=get_password_hash(password))
            session.add(config)
        else:
            config.value = get_password_hash(password)
        
        session.commit()
    
    def _get_admin_password_hash(self) -> str | None:
        """Get stored admin password hash."""
        from db import get_session, Config
        session = get_session(self.db_path)
        config = session.query(Config).filter_by(key="admin_password_hash").first()
        return config.value if config else None
    
    def generate_token(self, username: str = "admin") -> str:
        """Generate an access token."""
        return create_access_token({"sub": username})


class GitHubAppAuth:
    """GitHub App authentication (recommended for 2026)."""
    
    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
    
    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        now = int(datetime.utcnow().timestamp())
        payload = {
            "iat": now,
            "exp": now + (10 * 60),  # 10 minutes
            "iss": self.app_id,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    async def get_installation_token(
        self, installation_id: str, client: "GitHubClient"
    ) -> str:
        """Get installation access token."""
        jwt_token = self.generate_jwt()
        # In production, use the JWT to get installation token
        # This is a simplified version
        return jwt_token