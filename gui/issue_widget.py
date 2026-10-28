"""
Issue / Return Widget — Circulation Desk Panel.
Course: BBAT104 — Total Quality Management.

Features:
  - Issue a book: member search + book search, eligibility validation, due date display
  - Return a book: loan table with one-click return, auto fine calculation
  - Overdue tracker: view all overdue loans, mark fine as paid
  - Fine summary: total collected vs outstanding
  - All actions logged to QualityLog with ms timing
"""

from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QDialog, QFormLayout, QSpinBox,
    QMessageBox, QFrame, QDialogButtonBox, QAbstractItemView,
    QTabWidget, QSizePolicy, QSplitter, QTextEdit,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from services.library_service import (
    issue_book, return_book, mark_fine_paid,
    get_all_loans, refresh_overdue_statuses,
    get_all_members, get_all_books,
)
from services.search_service import search_loans, search_members, search_books
from services.logger_service import get_logger

logger = get_logger("gui.issue_widget")

_BTN_PRIMARY = "background-color:#2563EB;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_SUCCESS = "background-color:#10B981;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_DANGER  = "background-color:#EF4444;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"
_BTN_WARN    = "background-color:#F59E0B;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"


# ══════════════════════════════════════════════════════════════════════════════
# ISSUE BOOK DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class IssueBookDialog(QDialog):
    """
    Dialog to select a member and a book, validate eligibility, then confirm issue.
    """

    def __init__(self, processed_by: str = "Librarian", parent=None):
        super().__init__(parent)
        self.processed_by = processed_by
        self.selected_member_id = None
        self.selected_book_id   = None
        self.setWindowTitle("Issue Book to Member")
        self.setMinimumWidth(620)
        self.setMinimumHeight(540)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title_lbl = QLabel("Issue Book — Circulation Desk")
        title_lbl.setStyleSheet("font-size:18px;font-weight:800;color:#0F172A;")
        layout.addWidget(title_lbl)

        sub = QLabel("Search and select a member, then search and select a book to issue.")
        sub.setStyleSheet("color:#64748B;font-size:13px;")
        layout.addWidget(sub)

        # ── Member search ──────────────────────────────────────────────────
        m_frame = QFrame()
        m_frame.setStyleSheet("QFrame{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:8px;}")
        m_layout = QVBoxLayout(m_frame)
        m_layout.setSpacing(6)
        m_lbl = QLabel("Step 1: Select Member")
        m_lbl.setStyleSheet("font-weight:700;color:#0F172A;font-size:14px;")
        m_layout.addWidget(m_lbl)
        self.member_search = QLineEdit()
        self.member_search.setPlaceholderText("Type member name or USN...")
        self.member_search.textChanged.connect(self._search_members)
        m_layout.addWidget(self.member_search)
        self.member_table = QTableWidget()
        self.member_table.setColumnCount(5)
        self.member_table.setHorizontalHeaderLabels(["ID", "USN", "Name", "Dept", "Status"])
        self.member_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.member_table.verticalHeader().setVisible(False)
        self.member_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.member_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.member_table.setMaximumHeight(140)
        self.member_table.clicked.connect(self._member_selected)
        m_layout.addWidget(self.member_table)
        self.member_info_lbl = QLabel("No member selected")
        self.member_info_lbl.setStyleSheet("color:#64748B;font-size:12px;padding:4px 0;")
        m_layout.addWidget(self.member_info_lbl)
        layout.addWidget(m_frame)

        # ── Book search ────────────────────────────────────────────────────
        b_frame = QFrame()
        b_frame.setStyleSheet("QFrame{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:8px;}")
        b_layout = QVBoxLayout(b_frame)
        b_layout.setSpacing(6)
        b_lbl = QLabel("Step 2: Select Available Book")
        b_lbl.setStyleSheet("font-weight:700;color:#0F172A;font-size:14px;")
        b_layout.addWidget(b_lbl)
        self.book_search = QLineEdit()
        self.book_search.setPlaceholderText("Type book title, author or ISBN...")
        self.book_search.textChanged.connect(self._search_books)
        b_layout.addWidget(self.book_search)
        self.book_table = QTableWidget()
        self.book_table.setColumnCount(5)
        self.book_table.setHorizontalHeaderLabels(["ID", "Title", "Author", "Category", "Avail"])
        self.book_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.book_table.verticalHeader().setVisible(False)
        self.book_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.book_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.book_table.setMaximumHeight(140)
        self.book_table.clicked.connect(self._book_selected)
        b_layout.addWidget(self.book_table)
        self.book_info_lbl = QLabel("No book selected")
        self.book_info_lbl.setStyleSheet("color:#64748B;font-size:12px;padding:4px 0;")
        b_layout.addWidget(self.book_info_lbl)
        layout.addWidget(b_frame)

        # ── Due date info ──────────────────────────────────────────────────
        self.due_lbl = QLabel(f"Due date will be: {date.today().strftime('%Y-%m-%d')} + 14 days loan period")
        self.due_lbl.setStyleSheet("color:#2563EB;font-weight:600;font-size:13px;")
        layout.addWidget(self.due_lbl)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Issue Book")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(_BTN_SUCCESS)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet("padding:8px 14px;border-radius:6px;")
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Load initial data
        self._search_members("")
        self._search_books("")

    def _search_members(self, text: str):
        result = search_members(query=text, status="Active", page=1, page_size=30)
        members = result["results"]
        self.member_table.setRowCount(len(members))
        for row, m in enumerate(members):
            for col, val in enumerate([m["id"], m["usn"], m["name"], m["department"], m["status"]]):
                it = QTableWidgetItem(str(val))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if m["status"] == "Suspended":
                    it.setForeground(QColor("#EF4444"))
                self.member_table.setItem(row, col, it)

    def _search_books(self, text: str):
        result = search_books(query=text, availability="Available", page=1, page_size=30)
        books = result["results"]
        self.book_table.setRowCount(len(books))
        for row, b in enumerate(books):
            for col, val in enumerate([b["id"], b["title"][:40], b["author"][:25], b["category"], b["available_copies"]]):
                it = QTableWidgetItem(str(val))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.book_table.setItem(row, col, it)

    def _member_selected(self, idx):
        row = idx.row()
        try:
            self.selected_member_id = int(self.member_table.item(row, 0).text())
            name = self.member_table.item(row, 2).text()
            usn  = self.member_table.item(row, 1).text()
            status = self.member_table.item(row, 4).text()
            color = "#EF4444" if status == "Suspended" else "#10B981"
            self.member_info_lbl.setText(f"Selected: {name} ({usn}) — Status: {status}")
            self.member_info_lbl.setStyleSheet(f"color:{color};font-weight:600;font-size:12px;")
        except Exception:
            pass

    def _book_selected(self, idx):
        row = idx.row()
        try:
            self.selected_book_id = int(self.book_table.item(row, 0).text())
            title  = self.book_table.item(row, 1).text()
            author = self.book_table.item(row, 2).text()
            avail  = self.book_table.item(row, 4).text()
            from datetime import timedelta
            due = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
            self.book_info_lbl.setText(f"Selected: {title} by {author} ({avail} copies available)")
            self.book_info_lbl.setStyleSheet("color:#2563EB;font-weight:600;font-size:12px;")
            self.due_lbl.setText(f"Due date: {due} (14-day loan period per TQM SLA)")
        except Exception:
            pass

    def _validate_and_accept(self):
        if self.selected_member_id is None:
            QMessageBox.warning(self, "Selection Required", "Please select a member.")
            return
        if self.selected_book_id is None:
            QMessageBox.warning(self, "Selection Required", "Please select a book.")
            return
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
# ISSUE WIDGET — TABS: Active Loans | Return Book | Overdue & Fines
# ══════════════════════════════════════════════════════════════════════════════
class IssueWidget(QWidget):
    """
    Circulation desk panel with three tabs:
      1. Active Loans — search + one-click return
      2. Issue Book  — issue workflow dialog
      3. Overdue & Fines — overdue list with fine payment
    """

    LOAN_COLS = ["Loan #", "Book Title", "Member Name", "USN", "Borrow Date", "Due Date", "Status", "Fine (INR)"]

    def __init__(self, current_user: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {"username": "admin", "role": "Chief Librarian"}
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._refresh_loans_tab)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tb = QVBoxLayout(); tb.setSpacing(2)
        t = QLabel("Circulation Desk — Issue & Return")
        t.setStyleSheet("font-size:22px;font-weight:800;color:#0F172A;")
        s = QLabel("Issue books, process returns, track overdue loans and collect fines | TQM SLA: 14-day loan period, INR 5/day fine")
        s.setStyleSheet("font-size:13px;color:#64748B;")
        tb.addWidget(t); tb.addWidget(s)
        hdr.addLayout(tb); hdr.addStretch()
        self.issue_btn   = QPushButton("+ Issue Book");    self.issue_btn.setStyleSheet(_BTN_SUCCESS)
        self.refresh_btn = QPushButton("Refresh");         self.refresh_btn.setStyleSheet("padding:8px 14px;border-radius:6px;")
        hdr.addWidget(self.issue_btn); hdr.addWidget(self.refresh_btn)
        root.addLayout(hdr)

        # ── KPI summary bar ───────────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(12)
        self.kpi_active  = self._kpi_badge("Active Loans", "0", "#2563EB")
        self.kpi_overdue = self._kpi_badge("Overdue", "0", "#EF4444")
        self.kpi_fines   = self._kpi_badge("Outstanding Fines", "INR 0", "#F59E0B")
        self.kpi_today   = self._kpi_badge("Returned Today", "0", "#10B981")
        kpi_row.addWidget(self.kpi_active)
        kpi_row.addWidget(self.kpi_overdue)
        kpi_row.addWidget(self.kpi_fines)
        kpi_row.addWidget(self.kpi_today)
        kpi_row.addStretch()
        root.addLayout(kpi_row)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; font-weight: 600; }")

        # Tab 1: All Active Loans
        self.tabs.addTab(self._build_loans_tab(), "Active Loans")
        # Tab 2: Overdue & Fines
        self.tabs.addTab(self._build_overdue_tab(), "Overdue & Fines")
        # Tab 3: All Loan History
        self.tabs.addTab(self._build_history_tab(), "Full History")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

        # Connect buttons
        self.issue_btn.clicked.connect(self._issue_book_workflow)
        self.refresh_btn.clicked.connect(self.refresh_data)

    def _kpi_badge(self, title: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background:#FFFFFF;
                border:1px solid #E2E8F0;
                border-left:4px solid {color};
                border-radius:8px;
                padding:8px 14px;
                min-width:130px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("font-size:10px;font-weight:700;color:#64748B;letter-spacing:0.5px;")
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"font-size:20px;font-weight:800;color:#0F172A;")
        v_lbl.setObjectName(f"kpi_{title.replace(' ', '_')}")
        lay.addWidget(t_lbl)
        lay.addWidget(v_lbl)
        frame._value_lbl = v_lbl
        return frame

    def _build_loans_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)

        fbar = QHBoxLayout(); fbar.setSpacing(10)
        self.loan_search = QLineEdit()
        self.loan_search.setPlaceholderText("Search by book title, member name or USN...")
        self.loan_search.setStyleSheet("padding:8px 12px;border-radius:6px;border:1.5px solid #E2E8F0;")
        self.loan_search.textChanged.connect(lambda: self._search_timer.start(250))
        fbar.addWidget(self.loan_search, 4)
        self.loan_status_combo = QComboBox()
        self.loan_status_combo.addItems(["Active (Borrowed+Overdue)", "Borrowed", "Overdue", "All"])
        self.loan_status_combo.currentIndexChanged.connect(self._refresh_loans_tab)
        fbar.addWidget(self.loan_status_combo, 2)
        lay.addLayout(fbar)

        self.loans_table = self._make_loan_table()
        self.loans_table.doubleClicked.connect(self._return_selected_from_active)
        lay.addWidget(self.loans_table)

        bbar = QHBoxLayout(); bbar.setSpacing(10)
        self.loans_count_lbl = QLabel("0 loans")
        self.loans_count_lbl.setStyleSheet("color:#64748B;font-size:12px;")
        bbar.addWidget(self.loans_count_lbl); bbar.addStretch()
        self.return_btn = QPushButton("Return Selected Book")
        self.return_btn.setStyleSheet(_BTN_PRIMARY)
        self.return_btn.setToolTip("Double-click a loan row or select and click Return")
        self.return_btn.clicked.connect(self._return_selected_from_active)
        bbar.addWidget(self.return_btn)
        lay.addLayout(bbar)
        return w

    def _build_overdue_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)
        info = QLabel("All overdue loans — select a row and use the action buttons below.")
        info.setStyleSheet("color:#EF4444;font-weight:600;font-size:13px;padding:4px 0;")
        lay.addWidget(info)
        self.overdue_table = self._make_loan_table(extra_cols=["Days Overdue"])
        lay.addWidget(self.overdue_table)

        bbar = QHBoxLayout(); bbar.setSpacing(10)
        self.overdue_count_lbl = QLabel("0 overdue")
        self.overdue_count_lbl.setStyleSheet("color:#EF4444;font-weight:600;font-size:12px;")
        bbar.addWidget(self.overdue_count_lbl); bbar.addStretch()
        self.pay_fine_btn = QPushButton("Mark Fine Paid")
        self.pay_fine_btn.setStyleSheet(_BTN_WARN)
        self.return_overdue_btn = QPushButton("Return & Collect Fine")
        self.return_overdue_btn.setStyleSheet(_BTN_DANGER)
        bbar.addWidget(self.pay_fine_btn); bbar.addWidget(self.return_overdue_btn)
        lay.addLayout(bbar)
        self.pay_fine_btn.clicked.connect(self._pay_fine)
        self.return_overdue_btn.clicked.connect(self._return_overdue)
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)
        fbar = QHBoxLayout(); fbar.setSpacing(10)
        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("Search full loan history...")
        self.hist_search.setStyleSheet("padding:8px 12px;border-radius:6px;border:1.5px solid #E2E8F0;")
        self.hist_search.textChanged.connect(self._refresh_history_tab)
        fbar.addWidget(self.hist_search, 4)
        self.hist_status_combo = QComboBox()
        self.hist_status_combo.addItems(["All Status", "Borrowed", "Overdue", "Returned"])
        self.hist_status_combo.currentIndexChanged.connect(self._refresh_history_tab)
        fbar.addWidget(self.hist_status_combo, 2)
        lay.addLayout(fbar)
        self.history_table = self._make_loan_table()
        lay.addWidget(self.history_table)
        self.hist_count_lbl = QLabel("0 records")
        self.hist_count_lbl.setStyleSheet("color:#64748B;font-size:12px;")
        lay.addWidget(self.hist_count_lbl)
        return w

    def _make_loan_table(self, extra_cols: list = None) -> QTableWidget:
        cols = self.LOAN_COLS + (extra_cols or [])
        t = QTableWidget()
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setAlternatingRowColors(True)
        return t

    # ── Data loading ──────────────────────────────────────────────────────────

    def refresh_data(self):
        """Refresh overdue statuses and all tabs."""
        refresh_overdue_statuses(processed_by="system")
        self._refresh_kpis()
        self._refresh_loans_tab()
        self._refresh_overdue_tab()
        self._refresh_history_tab()

    def _refresh_kpis(self):
        from services.library_service import get_dashboard_kpis
        kpis = get_dashboard_kpis()
        self.kpi_active._value_lbl.setText(str(kpis["active_loans"]))
        self.kpi_overdue._value_lbl.setText(str(kpis["overdue_loans"]))
        outstanding = kpis["total_fines"] - kpis["fines_collected"]
        self.kpi_fines._value_lbl.setText(f"INR {outstanding:.0f}")
        # Count returned today
        today_str = date.today().strftime("%Y-%m-%d")
        all_loans = get_all_loans(status="Returned")
        today_ret = sum(1 for l in all_loans if l.get("return_date") == today_str)
        self.kpi_today._value_lbl.setText(str(today_ret))

    def _refresh_loans_tab(self):
        q = self.loan_search.text().strip()
        status_txt = self.loan_status_combo.currentText()
        if status_txt == "Active (Borrowed+Overdue)":
            # Fetch both and merge
            b_res = search_loans(query=q, status="Borrowed", page=1, page_size=300)
            o_res = search_loans(query=q, status="Overdue",  page=1, page_size=300)
            loans = b_res["results"] + o_res["results"]
        elif status_txt == "All":
            res = search_loans(query=q, page=1, page_size=500)
            loans = res["results"]
        else:
            res = search_loans(query=q, status=status_txt, page=1, page_size=300)
            loans = res["results"]
        self._fill_loan_table(self.loans_table, loans)
        self.loans_count_lbl.setText(f"{len(loans)} loans")

    def _refresh_overdue_tab(self):
        loans = get_all_loans(status="Overdue")
        self.overdue_table.setColumnCount(len(self.LOAN_COLS) + 1)
        self.overdue_table.setHorizontalHeaderLabels(self.LOAN_COLS + ["Days Overdue"])
        self._fill_loan_table(self.overdue_table, loans, show_overdue_days=True)
        self.overdue_count_lbl.setText(f"{len(loans)} overdue loans")

    def _refresh_history_tab(self):
        q = self.hist_search.text().strip()
        status_txt = self.hist_status_combo.currentText()
        status = "" if status_txt == "All Status" else status_txt
        res = search_loans(query=q, status=status, sort_by="borrow_date", sort_dir="desc",
                           page=1, page_size=500)
        self._fill_loan_table(self.history_table, res["results"])
        self.hist_count_lbl.setText(f"{res['total']} records")

    def _fill_loan_table(self, table: QTableWidget, loans: list, show_overdue_days: bool = False):
        STATUS_COLORS = {
            "Borrowed": QColor("#DBEAFE"),
            "Overdue":  QColor("#FEE2E2"),
            "Returned": QColor("#D1FAE5"),
        }
        table.setRowCount(len(loans))
        today = date.today()
        for row, l in enumerate(loans):
            def _item(text, align=Qt.AlignLeft):
                it = QTableWidgetItem(str(text))
                it.setTextAlignment(align | Qt.AlignVCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it
            table.setItem(row, 0, _item(l["id"], Qt.AlignCenter))
            table.setItem(row, 1, _item(l["book_title"]))
            table.setItem(row, 2, _item(l["member_name"]))
            table.setItem(row, 3, _item(l["member_usn"]))
            table.setItem(row, 4, _item(l["borrow_date"]))
            table.setItem(row, 5, _item(l["due_date"]))

            st_item = _item(l["status"], Qt.AlignCenter)
            st_item.setBackground(STATUS_COLORS.get(l["status"], QColor("#F8FAFC")))
            if l["status"] == "Overdue":
                st_item.setForeground(QColor("#EF4444"))
                st_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            table.setItem(row, 6, st_item)

            fine = l["fine_amount"]
            fine_item = _item(f"{fine:.2f}", Qt.AlignRight)
            if fine > 0 and not l.get("fine_paid"):
                fine_item.setForeground(QColor("#EF4444"))
                fine_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            elif fine > 0 and l.get("fine_paid"):
                fine_item.setForeground(QColor("#10B981"))
                fine_item.setText(f"{fine:.2f} (Paid)")
            table.setItem(row, 7, fine_item)

            if show_overdue_days and table.columnCount() > 8:
                try:
                    due = date.fromisoformat(l["due_date"])
                    days = max(0, (today - due).days)
                    d_item = _item(str(days) if days > 0 else "—", Qt.AlignCenter)
                    if days > 0:
                        d_item.setForeground(QColor("#EF4444"))
                        d_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
                    table.setItem(row, 8, d_item)
                except Exception:
                    pass

    def _on_tab_changed(self, idx: int):
        if idx == 1:
            self._refresh_overdue_tab()
        elif idx == 2:
            self._refresh_history_tab()

    # ── Action handlers ───────────────────────────────────────────────────────

    def _issue_book_workflow(self):
        dlg = IssueBookDialog(
            processed_by=self.current_user.get("username", "admin"),
            parent=self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        ok, loan_d, msg = issue_book(
            book_id=dlg.selected_book_id,
            member_id=dlg.selected_member_id,
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Book Issued", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Issue Failed", msg)

    def _return_selected_from_active(self):
        self._process_return(self.loans_table)

    def _return_overdue(self):
        self._process_return(self.overdue_table, fine_paid=True)

    def _process_return(self, table: QTableWidget, fine_paid: bool = False):
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a loan row to return.")
            return
        try:
            loan_id = int(table.item(row, 0).text())
        except Exception:
            QMessageBox.warning(self, "Error", "Could not read loan ID from selection.")
            return

        ok, _, msg = return_book(
            loan_id=loan_id,
            processed_by=self.current_user.get("username", "admin"),
            fine_paid=fine_paid,
        )
        if ok:
            QMessageBox.information(self, "Return Processed", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Return Failed", msg)

    def _pay_fine(self):
        row = self.overdue_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an overdue loan.")
            return
        try:
            loan_id = int(self.overdue_table.item(row, 0).text())
        except Exception:
            return
        ok, msg = mark_fine_paid(
            loan_id=loan_id,
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Fine Collected", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)
