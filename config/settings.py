"""
Centralized Configuration & Settings for Library Management System (TQM Edition).
Course: BBAT104 - Total Quality Management.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
REPORTS_DIR = EXPORTS_DIR  # Compatibility alias
CONFIG_DIR = BASE_DIR / "config"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration (SQLite via SQLAlchemy)
DATABASE_FILE = DATA_DIR / "campus_tqm.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Centralized Log File
LOG_FILE = LOGS_DIR / "app.log"

# Application Metadata
APP_NAME = "Library Management System"
APP_SUBTITLE = "TQM Automated Payroll & Performance System"
COURSE_NAME = "BBAT104 (Total Quality Management)"
APP_VERSION = "2.1.0"
ORGANIZATION = "Engineering College TQM Quality Cell"

# Security & Encryption
BCRYPT_ROUNDS = 12
SECRET_KEY = os.getenv("SECRET_KEY", "tqm-super-secret-key-bbat104-library-system")

# Total Quality Management (TQM) Parameters & Benchmarks
TQM_CONFIG = {
    "LOAN_PERIOD_DAYS": 14,             # Academic loan SLA window
    "FINE_PER_DAY": 5.0,                # Standardized fine per overdue day (INR)
    "MAX_BOOKS_PER_MEMBER": 4,          # Error-prevention limit on simultaneous loans
    "HOURLY_PAY_RATE": 120.0,           # Standard staff shift rate (INR/hr)
    "OVERTIME_MULTIPLIER": 1.5,         # Process automation multiplier for OT hours
    "TAX_DEDUCTION_RATE": 0.05,         # 5% standard PF/tax deduction
    "TARGET_ON_TIME_RETURN_RATE": 90.0, # TQM SLA: >= 90% books returned on time
    "DEFECT_TOLERANCE_RATE": 3.0,       # TQM Six Sigma tolerance: <= 3% book inventory defects
    "MAX_QUERY_LATENCY_MS": 100.0,      # Quality SLA: DB query latency target < 100ms
}

# Theme Color Palette (Modern Executive Slate + Royal Indigo)
THEME_COLORS = {
    "bg_main": "#F8FAFC",
    "bg_card": "#FFFFFF",
    "bg_sidebar": "#0F172A",
    "bg_sidebar_hover": "#1E293B",
    "sidebar_active": "#2563EB",
    "primary": "#2563EB",
    "primary_dark": "#1D4ED8",
    "primary_light": "#DBEAFE",
    "secondary": "#64748B",
    "text_primary": "#0F172A",
    "text_muted": "#64748B",
    "text_light": "#F8FAFC",
    "border": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "accent_purple": "#8B5CF6",
}
