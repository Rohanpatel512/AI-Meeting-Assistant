import bcrypt 
from datetime import datetime, timezone, timedelta
import jwt 
from app.core.config import JWT_SECRET, JWT_ALGORITHM

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against a hashed password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(user_id: int) -> str:
    """
    Creates a valid access token with a standard JWT expiration claim.
    """
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token


def refresh_access_token(user_id: int) -> str:
    """
    Generates a replacement access token after an expired session.
    """
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token