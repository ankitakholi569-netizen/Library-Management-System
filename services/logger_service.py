"""
TQM Centralized Logging & Quality Audit Service.
Course: BBAT104 - Total Quality Management.
Features:
- Dual-target rotating file logging to logs/app.log and terminal
- TQM Continuous Improvement Ledger integration (QualityLog model)
- Millisecond performance latency timer context manager for quality SLAs
"""

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from typing import Optional

from config.settings import LOG_FILE, TQM_CONFIG
from database.db import get_db
from database.models import QualityLog

# Ensure directory for logs exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Central log formatter
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Root / Library System Logger Setup
_root_logger = logging.getLogger("LibrarySystem")
_root_logger.setLevel(logging.INFO)

if not _root_logger.handlers:
    # 1. Rotating File Handler (Max 5MB per file, 5 backups)
    file_handler = RotatingFileHandler(
        str(LOG_FILE),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    _root_logger.addHandler(file_handler)

    # 2. Console Stream Handler (UTF-8 to handle ₹, ©, and other Unicode safely)
    import io
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    console_handler = logging.StreamHandler(utf8_stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    _root_logger.addHandler(console_handler)


def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a configured child logger under the centralized LibrarySystem hierarchy.
    """
    return logging.getLogger(f"LibrarySystem.{module_name}")


logger = get_logger("quality_service")


def log_quality_event(
    module: str,
    action: str,
    status: str = "SUCCESS",
    latency_ms: float = 0.0,
    details: str = "",
    remedial_action: str = "Standard Operating Procedure (SOP) verified",
) -> Optional[int]:
    """
    Dual-writes a quality event to logs/app.log and the SQLite QualityLog ledger.
    Aligns with TQM Principle: Evidence-based Decision Making & Traceability.
    """
    log_msg = f"[{module}] {action} -> Status: {status} ({latency_ms:.2f}ms) | {details}"
    if status in ("DEFECT", "ERROR", "FAILURE"):
        logger.error(log_msg)
    elif status in ("WARNING", "SLA_BREACH"):
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    # Persist to QualityLog DB ledger
    try:
        with get_db() as db:
            q_log = QualityLog(
                module=module.upper(),
                action=action.upper(),
                status=status.upper(),
                execution_time_ms=round(latency_ms, 2),
                details=details[:250],
                remedial_action=remedial_action[:250],
            )
            db.add(q_log)
            db.flush()
            return q_log.id
    except Exception as exc:
        logger.error(f"Failed to record QualityLog entry in database: {exc}")
        return None


@contextmanager
def timed_operation(
    module: str,
    action: str,
    details: str = "",
    remedial_action: str = "Standard Operating Procedure (SOP) verified",
):
    """
    Context manager to monitor operational latency against TQM SLA thresholds.
    Measures duration in milliseconds and records to QualityLog ledger.
    """
    start_time = time.perf_counter()
    status = "SUCCESS"
    captured_error = None

    try:
        yield
    except Exception as exc:
        status = "DEFECT"
        captured_error = exc
        details = f"Exception: {str(exc)} | {details}"
        raise
    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        sla_threshold = TQM_CONFIG.get("MAX_QUERY_LATENCY_MS", 100.0)

        # Check for SLA breach if no defect occurred
        if status == "SUCCESS" and latency_ms > sla_threshold:
            status = "SLA_BREACH"
            details = f"Latency {latency_ms:.1f}ms exceeded SLA ({sla_threshold:.1f}ms) | {details}"
            remedial_action = "Investigate DB index and optimize search query"

        log_quality_event(
            module=module,
            action=action,
            status=status,
            latency_ms=latency_ms,
            details=details,
            remedial_action=remedial_action,
        )
