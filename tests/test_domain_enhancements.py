"""
Unit & Integration Test Suite for TQM Domain Enhancements:
  1. ISBN Autofill & Metadata Fetching (FR-04 Catalog Manager)
  2. Hardware Barcode / RFID Buffer Hook (FR-03 Circulation Staff)
  3. Automated Hold / Waitlist Queue (FR-01 Student Kiosk)
  4. Real-time Telemetry Server-Sent Events (SSE) Stream

Course: BBAT104 - Total Quality Management.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import date

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use offscreen platform for headless Qt testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent

from database.db import get_db, init_db
from database.models import Book, Member, Loan, BookHold
from services.isbn_service import (
    clean_isbn,
    validate_isbn_format,
    fetch_isbn_metadata,
)
from services.library_service import (
    place_book_hold,
    get_book_holds,
    cancel_book_hold,
    issue_book,
    return_book,
)
from gui.issue_widget import BarcodeScannerFilter
from web.app import create_app


# ── 1. ISBN Autofill Tests ──────────────────────────────────────────────────

def test_isbn_cleaning_and_validation():
    assert clean_isbn("978-0-13-235088-4") == "9780132350884"
    assert clean_isbn("0-262-03384-4") == "0262033844"
    assert clean_isbn("  978 0134685991  ") == "9780134685991"

    assert validate_isbn_format("9780132350884") is True
    assert validate_isbn_format("0262033844") is True
    assert validate_isbn_format("12345") is False
    assert validate_isbn_format("INVALID_ISBN_XYZ") is False


def test_isbn_metadata_fetching():
    # Test Clean Code ISBN
    meta = fetch_isbn_metadata("978-0-13-235088-4")
    assert meta["found"] is True
    assert "Clean Code" in meta["title"]
    assert "Martin" in meta["author"]
    assert meta["year"] > 2000
    assert "latency_ms" in meta

    # Test Cache Hit (sub-millisecond)
    cached_meta = fetch_isbn_metadata("9780132350884")
    assert cached_meta["found"] is True
    assert cached_meta["title"] == meta["title"]

    # Test Invalid ISBN handling
    inv_meta = fetch_isbn_metadata("999-INV")
    assert inv_meta["found"] is False


# ── 2. Hardware Barcode Hook Tests ──────────────────────────────────────────

def test_hardware_barcode_scanner_burst():
    app = QApplication.instance() or QApplication(sys.argv)
    filter_obj = BarcodeScannerFilter(max_inter_char_ms=60.0)

    scanned_values = []
    filter_obj.barcode_scanned.connect(scanned_values.append)

    test_barcode = "9780132350884"

    # Simulate high-speed burst from USB laser scanner (<20ms per character)
    for char in test_barcode:
        event = QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, char)
        filter_obj.eventFilter(None, event)
        time.sleep(0.005)

    # Terminate with Enter key
    enter_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    filter_obj.eventFilter(None, enter_event)

    assert len(scanned_values) == 1, f"Expected 1 barcode emission, got {len(scanned_values)}"
    assert scanned_values[0] == test_barcode


def test_hardware_barcode_slow_typing_rejection():
    filter_obj = BarcodeScannerFilter(max_inter_char_ms=30.0)

    scanned_values = []
    filter_obj.barcode_scanned.connect(scanned_values.append)

    # Simulate slow human keyboard typing (>80ms per key)
    for char in "HUMAN_INPUT":
        event = QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, char)
        filter_obj.eventFilter(None, event)
        time.sleep(0.08)

    enter_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    filter_obj.eventFilter(None, enter_event)

    # Human typing pace exceeds scanner burst threshold, must not trigger hardware scan
    assert len(scanned_values) == 0


# ── 3. Automated Hold / Waitlist Queue Tests ─────────────────────────────────

def test_book_hold_queue_lifecycle():
    init_db()

    with get_db() as db:
        book = db.query(Book).first()
        member = db.query(Member).first()
        assert book is not None and member is not None
        book_id = book.id
        member_id = member.id

    # Place hold
    ok, hold_data, msg = place_book_hold(book_id, member_id, notes="Pytest reservation hold")
    assert ok is True
    assert hold_data is not None
    hold_id = hold_data["id"]

    # Duplicate hold prevention
    ok_dup, _, msg_dup = place_book_hold(book_id, member_id)
    assert ok_dup is False
    assert "already has an active" in msg_dup.lower()

    # Query active holds
    holds = get_book_holds(book_id=book_id, member_id=member_id)
    assert len(holds) >= 1
    assert any(h["id"] == hold_id for h in holds)

    # Cancel hold
    can_ok, can_msg = cancel_book_hold(hold_id)
    assert can_ok is True
    assert "cancelled" in can_msg.lower()


def test_hold_auto_notification_on_book_return():
    init_db()

    with get_db() as db:
        book = db.query(Book).first()
        member1 = db.query(Member).filter(Member.id == 1).first()
        member2 = db.query(Member).filter(Member.id == 2).first()
        assert book and member1 and member2
        book_id = book.id

        # Clean any existing holds on this book so our test hold is top of queue
        for h in db.query(BookHold).filter(BookHold.book_id == book_id).all():
            db.delete(h)
        db.commit()

        # Insert active test loan directly
        test_loan = Loan(
            book_id=book_id,
            member_id=member1.id,
            borrow_date=date.today(),
            due_date=date.today(),
            status="Borrowed",
            processed_by="Test Runner",
        )
        db.add(test_loan)

        # Place a pending hold for member2
        hold = BookHold(
            book_id=book_id,
            member_id=member2.id,
            request_date=date.today(),
            status="Pending",
            priority=1,
            notes="Waitlist testing",
        )
        db.add(hold)
        db.flush()
        loan_id = test_loan.id
        hold_id = hold.id

    # Return book -> Should trigger auto-notification hook for hold
    return_book(loan_id, processed_by="Desk Staff")

    with get_db() as db:
        checked_hold = db.get(BookHold, hold_id)
        assert checked_hold is not None
        # Hold must have transitioned to Ready
        assert checked_hold.status == "Ready"
        assert checked_hold.notified_at is not None
        assert checked_hold.expiry_date is not None


# ── 4. Web API Endpoints & SSE Stream Tests ─────────────────────────────────

def test_web_isbn_lookup_api():
    app = create_app()
    client = app.test_client()

    res = client.get("/api/isbn/lookup/9780132350884")
    assert res.status_code == 200
    data = res.get_json()
    assert data["found"] is True
    assert "Clean Code" in data["title"]


def test_web_kiosk_hold_api():
    app = create_app()
    client = app.test_client()

    # Get a book ID and clean any existing test hold for member 3
    with get_db() as db:
        book = db.query(Book).order_by(Book.id.desc()).first()
        book_id = book.id
        existing_holds = db.query(BookHold).filter(
            BookHold.book_id == book_id,
            BookHold.member_id == 3
        ).all()
        for h in existing_holds:
            db.delete(h)
        db.commit()

    # Place hold
    res = client.post("/api/kiosk/hold", json={
        "book_id": book_id,
        "member_id": 3,
        "notes": "Web API Test Hold"
    })
    assert res.status_code in (200, 201)
    data = res.get_json()
    assert data["success"] is True

    # List holds
    res_list = client.get(f"/api/kiosk/holds?book_id={book_id}")
    assert res_list.status_code == 200
    list_data = res_list.get_json()
    assert list_data["count"] >= 1


def test_web_sse_stream_kpi():
    app = create_app()
    client = app.test_client()

    res = client.get("/api/stream/kpi")
    assert res.status_code == 200
    assert "text/event-stream" in res.content_type

    # Read first SSE chunk
    chunk = next(res.response)
    chunk_str = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
    assert "event: kpi_update" in chunk_str
    assert "data: " in chunk_str
    assert "pending_holds" in chunk_str


if __name__ == "__main__":
    pytest.main(["-v", __file__])
