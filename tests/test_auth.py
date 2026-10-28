"""
Unit Test Suite for Authentication & Access Control (TQM Security SOP).
Course: BBAT104 - Total Quality Management.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import pytest
except ImportError:
    pytest = None

from database.seed import seed_database
from services.auth_service import (
    hash_password,
    verify_password,
    authenticate_user,
    create_user,
    change_password,
    get_all_users,
    get_staff_users,
    ROLE_CHIEF_LIBRARIAN,
    ROLE_ASSISTANT_LIBRARIAN,
    ROLE_LIBRARY_ASSISTANT,
    ROLE_STUDENT,
)

if pytest:
    @pytest.fixture(scope="module", autouse=True)
    def setup_db():
        seed_database()

def test_password_hashing():
    raw_pass = "SecurePass#2026"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPass123", hashed) is False

def test_admin_authentication():
    ok, user, msg = authenticate_user("admin", "admin123")
    assert ok is True
    assert user is not None
    assert user["username"] == "admin"
    assert user["role"] == ROLE_CHIEF_LIBRARIAN
    assert "password_hash" not in user

def test_invalid_credentials_rejection():
    ok, user, msg = authenticate_user("admin", "wrong_password_999")
    assert ok is False
    assert user is None
    assert "invalid" in msg.lower() or "rejected" in msg.lower() or "incorrect" in msg.lower()

    ok2, user2, msg2 = authenticate_user("nonexistent_user_xyz", "pass")
    assert ok2 is False
    assert user2 is None

def test_create_and_authenticate_user():
    import uuid
    uniq = uuid.uuid4().hex[:6]
    test_user = f"tester_{uniq}"
    ok, u_created, msg = create_user(
        username=test_user,
        password="TestPassword123!",
        full_name=f"Test Librarian {uniq}",
        role=ROLE_ASSISTANT_LIBRARIAN,
        hourly_rate=120.0,
    )
    assert ok is True
    assert u_created is not None
    user_id = u_created["id"]

    # Authenticate newly created user
    auth_ok, u_dict, _ = authenticate_user(test_user, "TestPassword123!")
    assert auth_ok is True
    assert u_dict["username"] == test_user
    assert u_dict["role"] == ROLE_ASSISTANT_LIBRARIAN

    # Change password (requires user_id, old_password, new_password)
    chg_ok, chg_msg = change_password(user_id, "TestPassword123!", "NewSecurePassword456!")
    assert chg_ok is True

    # Old password must fail
    old_ok, _, _ = authenticate_user(test_user, "TestPassword123!")
    assert old_ok is False

    # New password must succeed
    new_ok, new_dict, _ = authenticate_user(test_user, "NewSecurePassword456!")
    assert new_ok is True

def test_user_lists():
    all_users = get_all_users()
    assert len(all_users) >= 3
    staff_users = get_staff_users()
    assert len(staff_users) >= 3
    for s in staff_users:
        assert s["role"] in [ROLE_CHIEF_LIBRARIAN, ROLE_ASSISTANT_LIBRARIAN, ROLE_LIBRARY_ASSISTANT]

if __name__ == "__main__":
    seed_database()
    test_funcs = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    print(f"Running {len(test_funcs)} tests in {Path(__file__).name}...")
    for fn in test_funcs:
        fn()
        print(f"  [PASS] {fn.__name__}")
    print("All tests passed successfully!")
