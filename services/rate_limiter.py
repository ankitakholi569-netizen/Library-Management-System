"""
Rate Limiter Service for TQM Quality Gates.
Course: BBAT104 - Total Quality Management.

Enforces SLA Rate Limits:
- Student (Kiosk): 30 req/min (FR-01 TQM Quality Gate)
- Faculty Member: 120 req/min (FR-02 TQM Quality Gate)
"""

import time
import threading
from collections import defaultdict
from typing import Tuple, Dict, List
from services.logger_service import get_logger, log_quality_event

logger = get_logger("rate_limiter")


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check_rate_limit(
        self, client_id: str, max_requests: int, window_seconds: float = 60.0
    ) -> Tuple[bool, int, int, float]:
        """
        Validates request against allowed threshold within sliding window.
        Returns:
            (allowed: bool, current_count: int, remaining: int, retry_after: float)
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Purge timestamps older than the window
            timestamps = [t for t in self._requests[client_id] if t > window_start]
            current_count = len(timestamps)

            if current_count >= max_requests:
                earliest = timestamps[0] if timestamps else window_start
                retry_after = max(0.1, round(earliest + window_seconds - now, 2))
                log_quality_event(
                    "RATE_LIMIT",
                    "GATE_BREACH",
                    "WARNING",
                    details=f"Client '{client_id}' breached {max_requests} req/min limit (attempted {current_count + 1}).",
                    remedial_action="Applied temporary backoff throttle.",
                )
                self._requests[client_id] = timestamps
                return False, current_count, 0, retry_after

            # Record this request
            timestamps.append(now)
            self._requests[client_id] = timestamps
            remaining = max_requests - len(timestamps)
            return True, len(timestamps), remaining, 0.0

    def get_current_usage(self, client_id: str, window_seconds: float = 60.0) -> int:
        now = time.time()
        window_start = now - window_seconds
        with self._lock:
            timestamps = [t for t in self._requests.get(client_id, []) if t > window_start]
            self._requests[client_id] = timestamps
            return len(timestamps)

    def reset(self, client_id: str = None):
        with self._lock:
            if client_id:
                self._requests.pop(client_id, None)
            else:
                self._requests.clear()


# Global Singleton Limiter
limiter = SlidingWindowRateLimiter()


def check_student_kiosk_limit(client_id: str = "kiosk_default") -> Tuple[bool, int, int, float]:
    """TQM Quality Gate: 30 req/min for Student (Kiosk)."""
    return limiter.check_rate_limit(f"student_kiosk_{client_id}", max_requests=30)


def check_faculty_limit(client_id: str = "faculty_default") -> Tuple[bool, int, int, float]:
    """TQM Quality Gate: 120 req/min for Faculty Member."""
    return limiter.check_rate_limit(f"faculty_{client_id}", max_requests=120)

