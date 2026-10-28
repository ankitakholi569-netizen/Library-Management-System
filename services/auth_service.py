"""
Authentication & Access Control Service.
Course: BBAT104 - Total Quality Management.
Demonstrates TQM Principle: Standardization & Error Prevention in Access Security.
"""

from typing import Optional, Tuple, Dict, Any, List
import bcrypt
from sqlalchemy import select
from database.db import get_db
from database.models import User
from config.settings import BCRYPT_ROUNDS
from services.logger_service import get_logger, log_quality_event, timed_operation

logger = get_logger("auth_service")

# Standardized Role Constants
ROLE_CHIEF_LIBRARIAN = "Chief Librarian"
ROLE_ASSISTANT_LIBRARIAN = "Assistant Librarian"
ROLE_LIBRARY_ASSISTANT = "Library Assistant"
ROLE_STUDENT = "Student"

STAFF_ROLES = [ROLE_CHIEF_LIBRARIAN, ROLE_ASSISTANT_LIBRARIAN, ROLE_LIBRARY_ASSISTANT]


def hash_password(plain_password: str) -> str:
    """
    Hashes plain text password with salted bcrypt.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies plain password against stored bcrypt hash.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Validates user credentials against database.
    Returns: (success_bool, user_dict, message)
    """
    username = (username or "").strip()
    if not username or not password:
        return False, None, "Username and password are required."

    with timed_operation("AUTH", "USER_LOGIN", details=f"User: {username}"):
        with get_db() as db:
            user = db.scalar(select(User).where(User.username == username))
            if not user:
                logger.warning(f"Authentication failed: Unknown username '{username}'")
                return False, None, "Invalid credentials. User not found."

            if not user.is_active:
                logger.warning(f"Authentication rejected: User '{username}' account is deactivated.")
                return False, None, "Account is disabled. Contact system administrator."

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password for user '{username}'")
                return False, None, "Invalid username or password."

            user_data = user.to_dict()
            logger.info(f"User '{username}' ({user.role}) authenticated successfully.")
            return True, user_data, "Authentication successful."


def create_user(
    username: str,
    password: str,
    full_name: str,
    role: str = ROLE_LIBRARY_ASSISTANT,
    email: str = "",
    department: str = "Library Administration",
    hourly_rate: float = 120.0,
    base_salary: float = 24000.0,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Creates a new user record with validation.
    """
    username = (username or "").strip()
    full_name = (full_name or "").strip()

    if len(username) < 3:
        return False, None, "Username must be at least 3 characters long."
    if len(password) < 6:
        return False, None, "Password must be at least 6 characters long."
    if not full_name:
        return False, None, "Full name is required."

    with get_db() as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            return False, None, f"Username '{username}' is already taken."

        new_user = User(
            username=username,
            full_name=full_name,
            role=role,
            email=email.strip(),
            department=department.strip(),
            hourly_rate=float(hourly_rate),
            base_salary=float(base_salary),
            is_active=True,
        )
        new_user.set_password(password)
        db.add(new_user)
        db.flush()
        user_dict = new_user.to_dict()

    log_quality_event("AUTH", "CREATE_USER", "SUCCESS", details=f"User created: {username} ({role})")
    return True, user_dict, "User created successfully."


def change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Changes user password after verifying old password.
    """
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return False, "User not found."

        if not verify_password(old_password, user.hashed_password):
            return False, "Current password is incorrect."

        user.set_password(new_password)
        db.flush()

    log_quality_event("AUTH", "PASSWORD_CHANGE", "SUCCESS", details=f"User ID {user_id} password updated.")
    return True, "Password updated successfully."


def get_all_users() -> List[Dict[str, Any]]:
    """Retrieves all registered user accounts."""
    with get_db() as db:
        users = db.scalars(select(User).order_by(User.id)).all()
        return [u.to_dict() for u in users]


def get_staff_users() -> List[Dict[str, Any]]:
    """Retrieves staff and administrative users."""
    with get_db() as db:
        users = db.scalars(select(User).where(User.role.in_(STAFF_ROLES)).order_by(User.id)).all()
        return [u.to_dict() for u in users]
