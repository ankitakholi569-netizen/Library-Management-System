import bcrypt
from app.core.logger import get_logger

logger = get_logger("security")

def hash_password(plain_text_password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a generated salt.
    Prevents storage of cleartext passwords (TQM Data Security & Error Prevention).
    """
    if not plain_text_password:
        raise ValueError("Password cannot be empty.")
    
    # bcrypt requires bytes
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(plain_text_password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")

def verify_password(plain_text_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a stored bcrypt hash.
    Safe against timing attacks.
    """
    if not plain_text_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_text_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification encountered error: {e}")
        return False
