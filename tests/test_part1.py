"""
========================================================================================
TQM SYSTEM VERIFICATION — PART 1: CORE ENGINE & SECURITY
========================================================================================
Run this script to verify:
  1. Application Configuration & Directory Creation (Standardization)
  2. Rotating File Logger (Quality Monitoring & Error Logging)
  3. Bcrypt Password Hashing & Verification (Data Security & Error Prevention)
========================================================================================
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure safe output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_stage_1():
    print("=" * 75)
    print("RUNNING TQM VERIFICATION -- PART 1: ENVIRONMENT & SECURITY")
    print("=" * 75)

    # 1. Test Config & Runtime Folders
    print("\n[Step 1/3] Testing Configuration & Directories...")
    try:
        from app.config import (
            APP_NAME, APP_VERSION, DATA_DIR, LOGS_DIR, REPORTS_DIR, TQM_CONFIG
        )
        assert DATA_DIR.exists(), f"Missing directory: {DATA_DIR}"
        assert LOGS_DIR.exists(), f"Missing directory: {LOGS_DIR}"
        assert REPORTS_DIR.exists(), f"Missing directory: {REPORTS_DIR}"
        print(f"  [OK] Application Title : {APP_NAME} (v{APP_VERSION})")
        print(f"  [OK] Data Directory    : {DATA_DIR}")
        print(f"  [OK] Logs Directory    : {LOGS_DIR}")
        print(f"  [OK] Reports Directory : {REPORTS_DIR}")
        print(f"  [OK] TQM Loan SLA      : {TQM_CONFIG['LOAN_PERIOD_DAYS']} days")
        print(f"  [OK] TQM Fine Rate     : Rs. {TQM_CONFIG['FINE_PER_DAY']}/day")
    except Exception as e:
        print(f"  [FAILED] Config Error: {e}")
        return False

    # 2. Test Centralized Logger
    print("\n[Step 2/3] Testing Centralized Rotating Logger...")
    try:
        from app.core.logger import system_logger, get_logger
        test_log = get_logger("verification")
        test_log.info("TQM Audit Trail: Verification test event logged.")
        log_file = LOGS_DIR / "tqm_system.log"
        assert log_file.exists(), f"Log file was not created: {log_file}"
        print(f"  [OK] Logger initialized successfully")
        print(f"  [OK] Rotating log file confirmed at: {log_file}")
    except Exception as e:
        print(f"  [FAILED] Logger Error: {e}")
        return False

    # 3. Test Bcrypt Security Engine
    print("\n[Step 3/3] Testing Bcrypt Salted Password Hashing...")
    try:
        from app.core.security import hash_password, verify_password
        plain_pw = "admin123"
        hashed_pw = hash_password(plain_pw)
        
        # Verify correct password
        is_valid = verify_password(plain_pw, hashed_pw)
        assert is_valid, "Bcrypt failed to verify valid password!"

        # Verify incorrect password gets rejected (Error Prevention)
        is_invalid = verify_password("wrong_password", hashed_pw)
        assert not is_invalid, "Bcrypt failed to reject invalid password!"

        print(f"  [OK] Plain password    : {plain_pw}")
        print(f"  [OK] Hashed with salt  : {hashed_pw[:25]}... (length: {len(hashed_pw)})")
        print(f"  [OK] Password matches  : Yes ({is_valid})")
        print(f"  [OK] Rejects wrong pass: Yes (Properly Rejected)")
    except Exception as e:
        print(f"  [FAILED] Security Error: {e}")
        return False

    print("\n" + "=" * 75)
    print(">>> PART 1 ALL CHECKS PASSED: SYSTEM READY FOR PART 2 <<<")
    print("=" * 75)
    return True

if __name__ == "__main__":
    success = test_stage_1()
    sys.exit(0 if success else 1)
