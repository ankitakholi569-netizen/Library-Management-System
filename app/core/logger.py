import logging
from logging.handlers import RotatingFileHandler
import sys
from app.config import LOGS_DIR

# Standardized TQM Log Format: Timestamp | Level | Logger | Function:Line | Message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level=logging.INFO) -> logging.Logger:
    """
    Initializes centralized application logging with both console and rotating file output.
    Demonstrates TQM Principle: Standardization and Quality Monitoring.
    """
    root_logger = logging.getLogger("CampusLib")
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if root_logger.hasHandlers():
        return root_logger

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Console Stream Handler (Developer Visibility)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (Persistent TQM Audit Trail)
    # 5MB per file, keeping 5 historical backup cycles
    log_file_path = LOGS_DIR / "tqm_system.log"
    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger

def get_logger(module_name: str) -> logging.Logger:
    """Returns a namespaced child logger for modular tracking."""
    return logging.getLogger(f"CampusLib.{module_name}")

# Initialize system logger on module load
system_logger = setup_logging()
