"""
Configuration package for the Library Management System.
"""
from config.settings import (
    BASE_DIR,
    DATA_DIR,
    LOGS_DIR,
    EXPORTS_DIR,
    REPORTS_DIR,
    DATABASE_FILE,
    DATABASE_URL,
    LOG_FILE,
    APP_NAME,
    APP_VERSION,
    COURSE_NAME,
    TQM_CONFIG,
    THEME_COLORS,
    BCRYPT_ROUNDS,
    SECRET_KEY,
)

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "EXPORTS_DIR",
    "REPORTS_DIR",
    "DATABASE_FILE",
    "DATABASE_URL",
    "LOG_FILE",
    "APP_NAME",
    "APP_VERSION",
    "COURSE_NAME",
    "TQM_CONFIG",
    "THEME_COLORS",
    "BCRYPT_ROUNDS",
    "SECRET_KEY",
]
