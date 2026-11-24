"""
test_role_catalog_manager.py
=============================
Verifies that:
1. Book Catalog is present in Catalog Manager, NOT in Admin panel.
2. Circulation Desk is in Catalog Manager, enabling Issue and Return of books.
3. Catalog Manager has ONLY Book Catalog, Circulation Desk, and Stock Ledger (no other views).
4. Issue and Return operations work seamlessly when processed by Catalog Manager.
"""

import pytest
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from services.library_service import issue_book, return_book, add_book, add_member

# Ensure QApplication exists for GUI testing
app = QApplication.instance() or QApplication([])

def test_catalog_manager_navigation():
    """Catalog Manager must have a unified Catalog & Circulation Hub and Stock Ledger."""
    catalog_user = {
        "username": "rahul_catalog",
        "full_name": "Rahul Verma",
        "role": "Catalog Manager",
    }
    win = MainWindow(current_user=catalog_user)
    assert win.stakeholder_persona == "Catalog Manager"
    
    # Extract nav button texts and indices
    navs = [(btn.text(), idx) for btn, idx in win.nav_buttons]
    assert len(navs) == 2, f"Catalog Manager has unified hub and stock ledger, got: {navs}"
    
    expected_indices = [1, 9]  # Unified Catalog & Circulation Hub, Stock Ledger & GRN
    actual_indices = [idx for _, idx in navs]
    assert actual_indices == expected_indices
    
    assert "Catalog & Circulation Hub" in navs[0][0]
    assert "Stock Ledger" in navs[1][0]
    
    # Default view must be the unified hub (1)
    assert win.stack.currentIndex() == 1

    # Verify that the unified hub (BooksWidget) combines both Add/Manage Book and Circulation
    hub = win.books_widget
    assert hasattr(hub, "add_btn"), "Hub must have Add Book button"
    assert hasattr(hub, "issue_btn"), "Hub must have Issue Book button"
    assert hasattr(hub, "return_btn"), "Hub must have Return Book button"
    assert hasattr(hub, "table"), "Hub must display Books Catalog table"
    assert hasattr(hub, "loans_table"), "Hub must display Circulation Loans table"
    assert hasattr(hub, "hub_tabs"), "Hub must have unified tab navigation"
    assert hub.hub_tabs.count() == 2


def test_admin_navigation_no_catalog_or_circulation():
    """Admin panel must NOT have Book Catalog or Circulation Desk in its navigation items."""
    admin_user = {
        "username": "admin",
        "full_name": "Dr. Anita Sharma",
        "role": "Chief Librarian",
    }
    win = MainWindow(current_user=admin_user)
    assert win.stakeholder_persona == "Library Admin"
    
    nav_indices = [idx for _, idx in win.nav_buttons]
    # Book catalog (1) and Circulation Desk (3) MUST NOT be in Admin nav
    assert 1 not in nav_indices, f"Admin panel must NOT contain Book Catalog (view 1)! Found: {nav_indices}"
    assert 3 not in nav_indices, f"Admin panel must NOT contain Circulation Desk (view 3)! Found: {nav_indices}"
    
    # Verify Admin has other modules
    assert 0 in nav_indices  # Executive Dashboard
    assert 2 in nav_indices  # Member Directory
    assert 9 in nav_indices  # Stock Ledger
    assert 10 in nav_indices # Daily Z-Report
    assert 4 in nav_indices  # Audit
    assert 5 in nav_indices  # Staff Shifts
    assert 6 in nav_indices  # Payroll Engine


def test_catalog_manager_issue_and_return():
    """Verifies that Catalog Manager can successfully issue and return books."""
    manager_uname = "rahul_catalog"
    import uuid
    uid = uuid.uuid4().hex[:6]

    # Create a fresh book & member for testing
    ok_b, book, _ = add_book(
        title=f"Catalog Manager Ops Book {uid}",
        author="Rahul Verma",
        isbn=f"978-0-{uid[:5]}",
        total_copies=5,
        shelf_location="Aisle 4 - Rack C",
        processed_by=manager_uname,
    )
    assert ok_b and book is not None

    ok_m, member, _ = add_member(
        name=f"Ops Student {uid}",
        usn=f"1MS24CS{uid[:3]}",
        email=f"ops_{uid}@msrit.edu",
        department="Computer Science",
        phone="9876543210",
        processed_by=manager_uname,
    )
    assert ok_m and member is not None

    # Catalog manager issues the book
    ok_issue, loan, msg_issue = issue_book(
        book_id=book["id"],
        member_id=member["id"],
        processed_by=manager_uname,
    )
    assert ok_issue is True, f"Catalog manager failed to issue book: {msg_issue}"
    assert loan is not None
    assert loan["status"] == "Borrowed"

    # Catalog manager returns the book
    ok_ret, ret_loan, msg_ret = return_book(
        loan_id=loan["id"],
        processed_by=manager_uname,
        fine_paid=True,
    )
    assert ok_ret is True, f"Catalog manager failed to return book: {msg_ret}"
    assert ret_loan is not None
    assert ret_loan["status"] == "Returned"
