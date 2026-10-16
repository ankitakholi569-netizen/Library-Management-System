"""
Circulation View — Circulation Desk Operations, Book Issues, Returns & Fine Settlements.
Demonstrates TQM Principle: SLA Compliance, Process Automation & Defect Prevention.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from sqlalchemy.orm import joinedload
from app.models.base import get_db
from app.models.book import Book
from app.models.member import Member
from app.models.loan import Loan
from app.ui.components.search_input import SearchInput
from app.ui.components.kpi_badge import KPIBadge
from app.services.circulation_service import issue_book, return_book, settle_fine, refresh_overdue_status
from app.core.logger import get_logger

logger = get_logger("ui.circulation")


class IssueBookDialog(QDialog):
    """Dialog for issuing a book to a registered library member."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Issue Book — Circulation Desk")
        self.setFixedWidth(460)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()

        # Members combo
        self.member_combo = QComboBox()
        # Books combo
        self.book_combo = QComboBox()

        with get_db() as db:
            members = db.query(Member).filter(Member.is_active == True).all()
            for m in members:
                self.member_combo.addItem(f"{m.name} ({m.usn} - {m.department})", m.id)

            books = db.query(Book).filter(Book.available_copies > 0).all()
            for b in books:
                self.book_combo.addItem(f"{b.title} [Avail: {b.available_copies}]", b.id)

        form.addRow("Select Student / Patron *:", self.member_combo)
        form.addRow("Select Available Book *:", self.book_combo)

        sla_info = QLabel("Loan SLA: 14 days standard duration. Fine rate: Rs. 5.0/day if overdue.")
        sla_info.setStyleSheet("color: #64748B; font-size: 11px;")
        form.addRow("", sla_info)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        issue_btn = QPushButton("Confirm Issue")
        issue_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px 14px;")
        issue_btn.clicked.connect(self._confirm_issue)

        btns.addWidget(cancel_btn)
        btns.addWidget(issue_btn)
        layout.addLayout(btns)

    def _confirm_issue(self):
        member_id = self.member_combo.currentData()
        book_id = self.book_combo.currentData()

        if not member_id or not book_id:
            QMessageBox.warning(self, "Selection Required", "Please select both a patron and an available book.")
            return

        res = issue_book(book_id, member_id, processed_by="Circulation Desk")
        if res["success"]:
            QMessageBox.information(self, "Success", res["message"])
            self.accept()
        else:
            QMessageBox.critical(self, "Issue Denied", res["message"])


class CirculationView(QWidget):
    """Circulation desk interface with real-time loan status, overdue warnings, and returns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_loans()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        t = QLabel("Circulation Desk & Loan Tracking")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        st = QLabel("Enforces 14-day SLA, automated overdue escalation, and return management")
        st.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(t)
        title_box.addWidget(st)
        header.addLayout(title_box)
        header.addStretch()

        self.refresh_overdue_btn = QPushButton("Refresh SLA Fines")
        self.refresh_overdue_btn.setStyleSheet("background-color: #F59E0B; color: white; font-weight: 600; padding: 8px 14px;")
        self.refresh_overdue_btn.clicked.connect(self._refresh_overdue)
        header.addWidget(self.refresh_overdue_btn)

        self.issue_btn = QPushButton("+ Issue New Book")
        self.issue_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 14px;")
        self.issue_btn.clicked.connect(self._open_issue_dialog)
        header.addWidget(self.issue_btn)

        layout.addLayout(header)

        # Filter bar
        filter_bar = QHBoxLayout()
        self.search_input = SearchInput("Filter loans by student name, USN, or book title...")
        self.search_input.textChanged.connect(self._filter_loans)
        filter_bar.addWidget(self.search_input, stretch=3)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Borrowed", "Overdue", "Returned"])
        self.status_filter.currentTextChanged.connect(self._filter_loans)
        filter_bar.addWidget(self.status_filter, stretch=1)

        layout.addLayout(filter_bar)

        # Loans Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Loan #", "Book Title", "Student (USN)", "Issue Date", "Due Date", "Status", "Fine (Rs.)", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_loans(self):
        with get_db() as db:
            self.loans = db.query(Loan).options(joinedload(Loan.book), joinedload(Loan.member)).order_by(Loan.id.desc()).all()
        self._filter_loans()

    def _filter_loans(self):
        query = self.search_input.text().strip().lower()
        stat = self.status_filter.currentText()

        filtered = []
        for l in self.loans:
            if stat != "All Statuses" and l.status != stat:
                continue
            bt = l.book.title.lower() if l.book else ""
            mn = l.member.name.lower() if l.member else ""
            usn = l.member.usn.lower() if l.member else ""
            if query and not (query in bt or query in mn or query in usn):
                continue
            filtered.append(l)

        self.table.setRowCount(len(filtered))
        for row, l in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(f"#{l.id}"))
            self.table.setItem(row, 1, QTableWidgetItem(l.book.title if l.book else "N/A"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{l.member.name} ({l.member.usn})" if l.member else "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(str(l.issue_date)))
            self.table.setItem(row, 4, QTableWidgetItem(str(l.due_date)))

            # Status Badge
            scheme = "success" if l.status == "Returned" else ("danger" if l.status == "Overdue" else "info")
            badge = KPIBadge(l.status, scheme)
            self.table.setCellWidget(row, 5, badge)

            # Fine
            fine_text = f"Rs. {l.fine_amount:.2f}" if l.fine_amount > 0 else "-"
            fine_item = QTableWidgetItem(fine_text)
            fine_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, fine_item)

            # Action button
            if l.status in ["Borrowed", "Overdue"]:
                act_btn = QPushButton("Return Book")
                act_btn.setStyleSheet("background-color: #10B981; color: white; padding: 4px 8px; font-size: 11px;")
                act_btn.clicked.connect(lambda _, lid=l.id: self._return_book(lid))
                self.table.setCellWidget(row, 7, act_btn)
            elif l.fine_amount > 0 and not l.fine_paid:
                settle_btn = QPushButton("Settle Fine")
                settle_btn.setStyleSheet("background-color: #F59E0B; color: white; padding: 4px 8px; font-size: 11px;")
                settle_btn.clicked.connect(lambda _, lid=l.id: self._settle_fine(lid))
                self.table.setCellWidget(row, 7, settle_btn)
            else:
                closed_lbl = QLabel("Completed")
                closed_lbl.setAlignment(Qt.AlignCenter)
                closed_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
                self.table.setCellWidget(row, 7, closed_lbl)

    def _open_issue_dialog(self):
        dlg = IssueBookDialog(parent=self)
        if dlg.exec():
            self.load_loans()

    def _return_book(self, loan_id: int):
        res = return_book(loan_id)
        if res["success"]:
            QMessageBox.information(self, "Return Processed", res["message"])
            self.load_loans()
        else:
            QMessageBox.warning(self, "Error", res["message"])

    def _settle_fine(self, loan_id: int):
        res = settle_fine(loan_id)
        if res["success"]:
            QMessageBox.information(self, "Fine Settled", res["message"])
            self.load_loans()
        else:
            QMessageBox.warning(self, "Error", res["message"])

    def _refresh_overdue(self):
        count = refresh_overdue_status()
        QMessageBox.information(self, "SLA Refresh Complete", f"Circulation scan complete.\nActive overdue loans detected: {count}")
        self.load_loans()
