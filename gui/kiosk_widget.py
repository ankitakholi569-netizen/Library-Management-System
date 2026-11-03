"""
Student Kiosk (FR-01) & Faculty Research Portal (FR-02) Desktop Widgets.
Course: BBAT104 - Total Quality Management.

SRS Specifications Implemented:
- FR-01: Zero-navigation Ctrl+K bar & sub-85ms search for Student (Kiosk) [TQM Quality Gate: 30 req/min]
- FR-02: Multi-attribute research filter & citation sort for Faculty Member [TQM Quality Gate: 120 req/min]
"""

import time
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from services.search_service import student_kiosk_search, faculty_research_search
from services.library_service import get_book_categories


# ==============================================================================
# 1. STUDENT KIOSK WIDGET (FR-01)
# ==============================================================================
class StudentKioskWidget(QWidget):
    """
    Student Self-Service Textbook Kiosk.
    FR-01: Zero-navigation Ctrl+K search bar with sub-85ms latency SLA.
    TQM Quality Gate: 30 req/min rate limit enforcement.
    """

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.client_id = self.current_user.get("username", "student_kiosk")
        self._setup_ui()
        self.refresh_search()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🎓 Student Textbook Kiosk (Self-Service)")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("FR-01: Instant Zero-Navigation Search • Sub-85ms Latency SLA • 30 req/min Quality Gate")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        # Telemetry Badges
        self.latency_badge = QLabel("Latency: 0.0 ms")
        self.latency_badge.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; font-weight: 700; "
            "padding: 6px 12px; border-radius: 6px; border: 1px solid #A7F3D0; font-size: 12px;"
        )
        self.rate_badge = QLabel("Rate Limit: 0 / 30 req/min")
        self.rate_badge.setStyleSheet(
            "background-color: #EFF6FF; color: #2563EB; font-weight: 700; "
            "padding: 6px 12px; border-radius: 6px; border: 1px solid #BFDBFE; font-size: 12px;"
        )
        header.addWidget(self.latency_badge)
        header.addWidget(self.rate_badge)
        layout.addLayout(header)

        # Ctrl+K Search Bar Frame
        search_card = QFrame()
        search_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 10px;")
        s_layout = QHBoxLayout(search_card)
        s_layout.setContentsMargins(10, 6, 10, 6)
        s_layout.setSpacing(10)

        s_icon = QLabel("🔍")
        s_icon.setStyleSheet("font-size: 16px;")
        s_layout.addWidget(s_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type title, author, or ISBN to search textbooks instantly... (Shortcut: Ctrl+K)")
        self.search_input.setStyleSheet("border: none; font-size: 14px; background: transparent; color: #0F172A;")
        self.search_input.textChanged.connect(self.refresh_search)
        s_layout.addWidget(self.search_input, 1)

        shortcut_pill = QLabel("Ctrl+K")
        shortcut_pill.setStyleSheet(
            "background-color: #F1F5F9; color: #475569; font-size: 11px; font-weight: 700; "
            "padding: 3px 8px; border-radius: 4px; border: 1px solid #CBD5E1;"
        )
        s_layout.addWidget(shortcut_pill)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("font-size: 11px; padding: 4px 10px; background-color: #E2E8F0; border-radius: 4px;")
        self.clear_btn.clicked.connect(lambda: self.search_input.clear())
        s_layout.addWidget(self.clear_btn)

        layout.addWidget(search_card)

        # Setup Ctrl+K Shortcut
        self.shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.shortcut.activated.connect(self._focus_search)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ISBN", "Textbook Title", "Author", "Category", "Year", "Shelf Location", "Available", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def refresh_search(self):
        query = self.search_input.text().strip()
        data = student_kiosk_search(query, client_id=self.client_id)

        if not data.get("success"):
            if data.get("rate_limit_breach"):
                self.rate_badge.setText("Rate: 30/30 (LIMIT REACHED)")
                self.rate_badge.setStyleSheet("background-color: #FEE2E2; color: #DC2626; font-weight: 700; padding: 6px 12px; border-radius: 6px;")
                QMessageBox.warning(self, "TQM Quality Gate Alert", data.get("error", "Rate limit exceeded."))
            return

        latency = data.get("latency_ms", 0.0)
        sla_pass = data.get("sla_pass", True)
        rate_info = data.get("rate_limit", {})

        # Update Telemetry Badges
        pass_text = "PASS < 85ms" if sla_pass else "BREACH > 85ms"
        bg_col = "#ECFDF5" if sla_pass else "#FEF3C7"
        fg_col = "#059669" if sla_pass else "#D97706"
        self.latency_badge.setText(f"Latency: {latency:.1f} ms ({pass_text})")
        self.latency_badge.setStyleSheet(f"background-color: {bg_col}; color: {fg_col}; font-weight: 700; padding: 6px 12px; border-radius: 6px;")

        self.rate_badge.setText(f"Rate: {rate_info.get('current_usage', 0)} / 30 req/min")

        results = data.get("results", [])
        self.table.setRowCount(len(results))

        for row, b in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(b.get("isbn", "")))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("author", "")))
            self.table.setItem(row, 3, QTableWidgetItem(b.get("category", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(b.get("year", ""))))
            self.table.setItem(row, 5, QTableWidgetItem(b.get("shelf_location", "")))

            avail = b.get("available_copies", 0)
            total = b.get("total_copies", 0)
            self.table.setItem(row, 6, QTableWidgetItem(f"{avail} of {total}"))

            status_item = QTableWidgetItem("In Stock" if avail > 0 else "Checked Out")
            status_item.setForeground(Qt.darkGreen if avail > 0 else Qt.darkRed)
            self.table.setItem(row, 7, status_item)


# ==============================================================================
# 2. FACULTY RESEARCH & CITATION PORTAL WIDGET (FR-02)
# ==============================================================================
class FacultyResearchWidget(QWidget):
    """
    Faculty Research & Citation Search Portal.
    FR-02: Multi-attribute research filter & citation sort.
    TQM Quality Gate: 120 req/min rate limit.
    """

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.client_id = self.current_user.get("username", "faculty_default")
        self._setup_ui()
        self.refresh_search()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🔬 Faculty Research & Citation Portal")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("FR-02: Multi-Attribute Research Filter • Citation Impact Sort • 120 req/min Quality Gate")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.latency_badge = QLabel("Latency: 0.0 ms")
        self.latency_badge.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; font-weight: 700; "
            "padding: 6px 12px; border-radius: 6px; border: 1px solid #A7F3D0; font-size: 12px;"
        )
        self.rate_badge = QLabel("Rate Limit: 0 / 120 req/min")
        self.rate_badge.setStyleSheet(
            "background-color: #EFF6FF; color: #2563EB; font-weight: 700; "
            "padding: 6px 12px; border-radius: 6px; border: 1px solid #BFDBFE; font-size: 12px;"
        )
        header.addWidget(self.latency_badge)
        header.addWidget(self.rate_badge)
        layout.addLayout(header)

        # Multi-Attribute Filter Card
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px;")
        f_layout = QVBoxLayout(filter_card)
        f_layout.setSpacing(10)

        # Row 1: Search query + Category
        r1 = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title, author, topic, or DOI...")
        self.search_input.setStyleSheet("padding: 8px; border: 1px solid #CBD5E1; border-radius: 6px; font-size: 13px;")
        self.search_input.textChanged.connect(self.refresh_search)
        r1.addWidget(self.search_input, 2)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        for cat in get_book_categories():
            self.category_combo.addItem(cat)
        self.category_combo.currentIndexChanged.connect(self.refresh_search)
        r1.addWidget(self.category_combo, 1)

        # Sort Order Dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("⭐ Sort by Citations (Highest Impact)", "citations")
        self.sort_combo.addItem("📅 Sort by Publication Year (Newest)", "year_desc")
        self.sort_combo.addItem("📅 Sort by Publication Year (Oldest)", "year_asc")
        self.sort_combo.addItem("🔤 Sort by Title (A-Z)", "title")
        self.sort_combo.currentIndexChanged.connect(self.refresh_search)
        r1.addWidget(self.sort_combo, 1)

        f_layout.addLayout(r1)

        # Row 2: Year Range + Peer Reviewed Flag
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Min Year:"))
        self.min_year = QSpinBox()
        self.min_year.setRange(1950, 2030)
        self.min_year.setValue(1990)
        self.min_year.valueChanged.connect(self.refresh_search)
        r2.addWidget(self.min_year)

        r2.addWidget(QLabel("Max Year:"))
        self.max_year = QSpinBox()
        self.max_year.setRange(1950, 2030)
        self.max_year.setValue(2026)
        self.max_year.valueChanged.connect(self.refresh_search)
        r2.addWidget(self.max_year)

        self.peer_reviewed_cb = QCheckBox("Peer-Reviewed Journals / Publications Only")
        self.peer_reviewed_cb.setStyleSheet("font-weight: 600; color: #334155;")
        self.peer_reviewed_cb.stateChanged.connect(self.refresh_search)
        r2.addWidget(self.peer_reviewed_cb)

        r2.addStretch()

        self.reset_btn = QPushButton("Reset Filters")
        self.reset_btn.setStyleSheet("padding: 4px 10px; background-color: #E2E8F0; border-radius: 4px;")
        self.reset_btn.clicked.connect(self._reset_filters)
        r2.addWidget(self.reset_btn)

        f_layout.addLayout(r2)
        layout.addWidget(filter_card)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Title / Paper", "Author", "Category", "Year", "Citations", "Peer Reviewed", "DOI / Identifier", "Available"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _reset_filters(self):
        self.search_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.min_year.setValue(1990)
        self.max_year.setValue(2026)
        self.peer_reviewed_cb.setChecked(False)
        self.refresh_search()

    def refresh_search(self):
        query = self.search_input.text().strip()
        cat = self.category_combo.currentText()
        if cat == "All Categories":
            cat = None
        sort_by = self.sort_combo.currentData() or "citations"
        min_y = self.min_year.value()
        max_y = self.max_year.value()
        peer_only = self.peer_reviewed_cb.isChecked()

        data = faculty_research_search(
            query=query,
            category=cat,
            min_year=min_y,
            max_year=max_y,
            peer_reviewed_only=peer_only,
            sort_by=sort_by,
            client_id=self.client_id
        )

        if not data.get("success"):
            if data.get("rate_limit_breach"):
                self.rate_badge.setText("Rate: 120/120 (LIMIT REACHED)")
                self.rate_badge.setStyleSheet("background-color: #FEE2E2; color: #DC2626; font-weight: 700; padding: 6px 12px; border-radius: 6px;")
                QMessageBox.warning(self, "TQM Quality Gate Alert", data.get("error", "Rate limit exceeded."))
            return

        latency = data.get("latency_ms", 0.0)
        rate_info = data.get("rate_limit", {})
        self.latency_badge.setText(f"Latency: {latency:.1f} ms")
        self.rate_badge.setText(f"Rate: {rate_info.get('current_usage', 0)} / 120 req/min")

        results = data.get("results", [])
        self.table.setRowCount(len(results))

        for row, b in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(b.get("title", "")))
            self.table.setItem(row, 1, QTableWidgetItem(b.get("author", "")))
            self.table.setItem(row, 2, QTableWidgetItem(b.get("category", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(b.get("year", ""))))

            cit_item = QTableWidgetItem(f"⭐ {b.get('citation_count', 0):,}")
            cit_item.setForeground(Qt.darkBlue)
            self.table.setItem(row, 4, cit_item)

            peer = "Yes (Verified)" if b.get("is_peer_reviewed") else "Standard"
            p_item = QTableWidgetItem(peer)
            p_item.setForeground(Qt.darkGreen if b.get("is_peer_reviewed") else Qt.gray)
            self.table.setItem(row, 5, p_item)

            self.table.setItem(row, 6, QTableWidgetItem(b.get("doi", "")))
            avail = b.get("available_copies", 0)
            total = b.get("total_copies", 0)
            self.table.setItem(row, 7, QTableWidgetItem(f"{avail}/{total}"))

