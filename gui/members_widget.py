"""
Members Widget — Full CRUD for Library Member Directory.
Course: BBAT104 — Total Quality Management.

Features:
  - Instant search by name / USN / email / phone
  - Department, status, membership-type filters
  - Add/Edit member dialogs with validation
  - Delete with active-loan guard
  - Borrow history panel (double-click member to view)
  - Member status suspend/activate toggle
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QDialog, QFormLayout, QSpinBox,
    QMessageBox, QFrame, QDialogButtonBox, QAbstractItemView,
    QSplitter, QTabWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from services.library_service import (
    get_all_members, get_member_by_id, get_member_departments,
    add_member, update_member, delete_member, get_member_loan_history,
)
from services.search_service import search_members
from services.logger_service import get_logger

logger = get_logger("gui.members_widget")

_BTN_PRIMARY = "background-color:#2563EB;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_SUCCESS = "background-color:#10B981;color:#fff;font-weight:700;padding:8px 16px;border-radius:6px;border:none;"
_BTN_DANGER  = "background-color:#EF4444;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"
_BTN_WARN    = "background-color:#F59E0B;color:#fff;font-weight:700;padding:8px 14px;border-radius:6px;border:none;"


# ══════════════════════════════════════════════════════════════════════════════
# ADD / EDIT MEMBER DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class MemberDialog(QDialog):
    """Modal dialog for adding or editing a library member."""

    DEPARTMENTS = ["CSE", "ECE", "ME", "CV", "MBA", "Physics", "Chemistry", "Mathematics", "Library Administration"]
    TYPES       = ["Student", "Faculty", "Staff", "Research Scholar"]

    def __init__(self, member_data: dict = None, parent=None):
        super().__init__(parent)
        self.member_data = member_data
        self.setWindowTitle("Register New Member" if not member_data else f"Edit Member — {member_data.get('usn', '')}")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()
        if member_data:
            self._populate(member_data)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        mode_title = "Register New Library Member" if not self.member_data else "Edit Member Record"
        title_lbl = QLabel(mode_title)
        title_lbl.setStyleSheet("font-size:18px;font-weight:800;color:#0F172A;")
        layout.addWidget(title_lbl)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.f_usn   = QLineEdit(); self.f_usn.setPlaceholderText("e.g. 1RV21CS001 or FAC-CSE-001")
        self.f_name  = QLineEdit(); self.f_name.setPlaceholderText("Full name")
        self.f_dept  = QComboBox(); self.f_dept.setEditable(True); self.f_dept.addItems(self.DEPARTMENTS)
        self.f_sem   = QSpinBox(); self.f_sem.setRange(0, 10); self.f_sem.setSpecialValueText("N/A (Faculty)")
        self.f_type  = QComboBox(); self.f_type.addItems(self.TYPES)
        self.f_email = QLineEdit(); self.f_email.setPlaceholderText("email@college.edu")
        self.f_phone = QLineEdit(); self.f_phone.setPlaceholderText("10-digit mobile number")
        self.f_status= QComboBox(); self.f_status.addItems(["Active", "Suspended"])

        form.addRow("USN / Member ID *", self.f_usn)
        form.addRow("Full Name *",       self.f_name)
        form.addRow("Department",        self.f_dept)
        form.addRow("Semester",          self.f_sem)
        form.addRow("Membership Type",   self.f_type)
        form.addRow("Email",             self.f_email)
        form.addRow("Phone",             self.f_phone)
        form.addRow("Status",            self.f_status)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Save).setStyleSheet(_BTN_PRIMARY)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet("padding:8px 14px;border-radius:6px;")
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate(self, d: dict):
        self.f_usn.setText(d.get("usn", ""))
        self.f_usn.setReadOnly(True)   # USN is immutable after creation
        self.f_usn.setStyleSheet("background:#F1F5F9;color:#64748B;padding:7px 12px;border-radius:6px;border:1px solid #E2E8F0;")
        self.f_name.setText(d.get("name", ""))
        idx = self.f_dept.findText(d.get("department", ""))
        if idx >= 0: self.f_dept.setCurrentIndex(idx)
        else: self.f_dept.setCurrentText(d.get("department", ""))
        self.f_sem.setValue(d.get("semester", 0))
        idx2 = self.f_type.findText(d.get("membership_type", "Student"))
        if idx2 >= 0: self.f_type.setCurrentIndex(idx2)
        self.f_email.setText(d.get("email", ""))
        self.f_phone.setText(d.get("phone", ""))
        idx3 = self.f_status.findText(d.get("status", "Active"))
        if idx3 >= 0: self.f_status.setCurrentIndex(idx3)

    def _validate_and_accept(self):
        if not self.f_usn.text().strip():
            QMessageBox.warning(self, "Validation Error", "USN / Member ID is required.")
            return
        if not self.f_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Member name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "usn":             self.f_usn.text().strip().upper(),
            "name":            self.f_name.text().strip(),
            "department":      self.f_dept.currentText().strip(),
            "semester":        self.f_sem.value(),
            "membership_type": self.f_type.currentText(),
            "email":           self.f_email.text().strip(),
            "phone":           self.f_phone.text().strip(),
            "status":          self.f_status.currentText(),
        }


# ══════════════════════════════════════════════════════════════════════════════
# BORROW HISTORY PANEL (embedded in Members view)
# ══════════════════════════════════════════════════════════════════════════════
class BorrowHistoryPanel(QWidget):
    """Compact borrow history table shown when a member is selected."""

    LOAN_COLS = ["Loan #", "Book Title", "Borrow Date", "Due Date", "Return Date", "Status", "Fine (INR)"]

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.title_lbl = QLabel("Select a member to view borrow history")
        self.title_lbl.setStyleSheet("font-weight:700;color:#0F172A;font-size:14px;padding:8px 0;")
        layout.addWidget(self.title_lbl)
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.LOAN_COLS))
        self.table.setHorizontalHeaderLabels(self.LOAN_COLS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_history(self, member_id: int, member_name: str):
        self.title_lbl.setText(f"Borrow History — {member_name}")
        history = get_member_loan_history(member_id)
        self.table.setRowCount(len(history))
        STATUS_COLORS = {"Borrowed": "#DBEAFE", "Overdue": "#FEE2E2", "Returned": "#D1FAE5"}
        for row, l in enumerate(history):
            def _item(txt, align=Qt.AlignLeft):
                it = QTableWidgetItem(str(txt))
                it.setTextAlignment(align | Qt.AlignVCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it
            self.table.setItem(row, 0, _item(l["id"], Qt.AlignCenter))
            self.table.setItem(row, 1, _item(l["book_title"]))
            self.table.setItem(row, 2, _item(l["borrow_date"]))
            self.table.setItem(row, 3, _item(l["due_date"]))
            self.table.setItem(row, 4, _item(l["return_date"] or "—", Qt.AlignCenter))
            status_item = _item(l["status"], Qt.AlignCenter)
            bg = STATUS_COLORS.get(l["status"], "#F8FAFC")
            status_item.setBackground(QColor(bg))
            self.table.setItem(row, 5, status_item)
            fine = l["fine_amount"]
            fine_item = _item(f"{fine:.2f}" if fine else "0.00", Qt.AlignRight)
            if fine > 0:
                fine_item.setForeground(QColor("#EF4444"))
                fine_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.table.setItem(row, 6, fine_item)


# ══════════════════════════════════════════════════════════════════════════════
# MEMBERS WIDGET — MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
class MembersWidget(QWidget):
    """Full CRUD Member directory with search, filters, and borrow history panel."""

    COLS = ["ID", "USN", "Name", "Department", "Semester", "Type", "Email", "Phone", "Active Loans", "Status"]

    def __init__(self, current_user: dict = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {"username": "admin", "role": "Chief Librarian"}
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(14)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tb = QVBoxLayout(); tb.setSpacing(2)
        t = QLabel("Member Directory")
        t.setStyleSheet("font-size:22px;font-weight:800;color:#0F172A;")
        s = QLabel("Register, search and manage student & faculty library members | View complete borrowing history")
        s.setStyleSheet("font-size:13px;color:#64748B;")
        tb.addWidget(t); tb.addWidget(s)
        hdr.addLayout(tb); hdr.addStretch()

        self.add_btn     = QPushButton("+ Register Member"); self.add_btn.setStyleSheet(_BTN_SUCCESS)
        self.refresh_btn = QPushButton("Refresh");           self.refresh_btn.setStyleSheet("padding:8px 14px;border-radius:6px;")
        hdr.addWidget(self.add_btn); hdr.addWidget(self.refresh_btn)
        root.addLayout(hdr)

        # ── Search + Filter bar ───────────────────────────────────────────────
        fbar = QHBoxLayout(); fbar.setSpacing(10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by Name, USN, Email or Phone...")
        self.search_box.setStyleSheet("padding:8px 12px;border-radius:6px;border:1.5px solid #E2E8F0;font-size:13px;")
        self.search_box.textChanged.connect(lambda: self._search_timer.start(250))
        fbar.addWidget(self.search_box, 4)

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("All Departments", "")
        self.dept_combo.currentIndexChanged.connect(self._do_search)
        fbar.addWidget(self.dept_combo, 2)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All Types", "Student", "Faculty", "Staff", "Research Scholar"])
        self.type_combo.currentIndexChanged.connect(self._do_search)
        fbar.addWidget(self.type_combo, 2)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Status", "Active", "Suspended"])
        self.status_combo.currentIndexChanged.connect(self._do_search)
        fbar.addWidget(self.status_combo, 1)

        self.kpi_lbl = QLabel("Search: —")
        self.kpi_lbl.setStyleSheet("color:#64748B;font-size:12px;padding-left:8px;")
        fbar.addWidget(self.kpi_lbl)
        root.addLayout(fbar)

        # ── Splitter: Member table + History panel ────────────────────────────
        splitter = QSplitter(Qt.Vertical)

        # Member table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.currentItemChanged.connect(self._on_row_changed)
        self.table.doubleClicked.connect(self._edit_selected)
        splitter.addWidget(self.table)

        # History panel
        self.history_panel = BorrowHistoryPanel()
        splitter.addWidget(self.history_panel)
        splitter.setSizes([380, 200])

        root.addWidget(splitter)

        # ── Bottom action bar ─────────────────────────────────────────────────
        bbar = QHBoxLayout(); bbar.setSpacing(10)
        self.count_lbl = QLabel("0 members")
        self.count_lbl.setStyleSheet("color:#64748B;font-size:12px;")
        bbar.addWidget(self.count_lbl); bbar.addStretch()
        self.edit_btn    = QPushButton("Edit Selected");     self.edit_btn.setStyleSheet(_BTN_PRIMARY)
        self.delete_btn  = QPushButton("Delete Selected");   self.delete_btn.setStyleSheet(_BTN_DANGER)
        self.suspend_btn = QPushButton("Suspend / Activate"); self.suspend_btn.setStyleSheet(_BTN_WARN)
        bbar.addWidget(self.edit_btn); bbar.addWidget(self.delete_btn); bbar.addWidget(self.suspend_btn)
        root.addLayout(bbar)

        self.add_btn.clicked.connect(self._add_member)
        self.edit_btn.clicked.connect(self._edit_selected)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.suspend_btn.clicked.connect(self._toggle_status)
        self.refresh_btn.clicked.connect(self.refresh_data)

    # ── Data operations ───────────────────────────────────────────────────────

    def refresh_data(self):
        depts = get_member_departments()
        cur_dept = self.dept_combo.currentData()
        self.dept_combo.blockSignals(True)
        self.dept_combo.clear()
        self.dept_combo.addItem("All Departments", "")
        for d in depts:
            self.dept_combo.addItem(d, d)
        idx = self.dept_combo.findData(cur_dept)
        self.dept_combo.setCurrentIndex(max(0, idx))
        self.dept_combo.blockSignals(False)
        self._do_search()

    def _do_search(self):
        query    = self.search_box.text().strip()
        dept     = self.dept_combo.currentData() or ""
        type_txt = self.type_combo.currentText()
        m_type   = "" if type_txt == "All Types" else type_txt
        stat_txt = self.status_combo.currentText()
        status   = "" if stat_txt == "All Status" else stat_txt

        result = search_members(
            query=query, department=dept,
            membership_type=m_type, status=status,
            sort_by="name", sort_dir="asc",
            page=1, page_size=500,
        )
        self._render_table(result["results"])
        ms = result["latency_ms"]
        color = "#10B981" if result["sla_ok"] else "#EF4444"
        sla   = "OK" if result["sla_ok"] else "BREACH"
        self.kpi_lbl.setText(f"Search: {ms:.1f}ms ({sla})")
        self.kpi_lbl.setStyleSheet(f"color:{color};font-size:12px;font-weight:600;padding-left:8px;")
        self.count_lbl.setText(f"{result['total']} members")

    def _render_table(self, members: list):
        self.table.setRowCount(len(members))
        STATUS_BG = {"Active": QColor("#D1FAE5"), "Suspended": QColor("#FEE2E2")}
        for row, m in enumerate(members):
            def _item(txt, align=Qt.AlignLeft):
                it = QTableWidgetItem(str(txt))
                it.setTextAlignment(align | Qt.AlignVCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                return it
            self.table.setItem(row, 0, _item(m["id"], Qt.AlignCenter))
            self.table.setItem(row, 1, _item(m["usn"]))
            self.table.setItem(row, 2, _item(m["name"]))
            self.table.setItem(row, 3, _item(m["department"]))
            self.table.setItem(row, 4, _item(m["semester"] if m["semester"] > 0 else "—", Qt.AlignCenter))
            self.table.setItem(row, 5, _item(m["membership_type"]))
            self.table.setItem(row, 6, _item(m["email"]))
            self.table.setItem(row, 7, _item(m["phone"]))
            loans_item = _item(str(m["active_loans"]), Qt.AlignCenter)
            if m["active_loans"] > 0:
                loans_item.setForeground(QColor("#2563EB"))
                loans_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.table.setItem(row, 8, loans_item)
            st_item = _item(m["status"], Qt.AlignCenter)
            st_item.setBackground(STATUS_BG.get(m["status"], QColor("#F8FAFC")))
            if m["status"] == "Suspended":
                st_item.setForeground(QColor("#EF4444"))
                st_item.setFont(QFont("Segoe UI", 11, QFont.Bold))
            self.table.setItem(row, 9, st_item)

    def _on_row_changed(self, current, _prev):
        if not current:
            return
        row = current.row()
        try:
            member_id   = int(self.table.item(row, 0).text())
            member_name = self.table.item(row, 2).text()
            self.history_panel.load_history(member_id, member_name)
        except Exception:
            pass

    def _selected_member_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a member row first.")
            return None
        try:
            return int(self.table.item(row, 0).text())
        except Exception:
            return None

    # ── CRUD handlers ─────────────────────────────────────────────────────────

    def _add_member(self):
        dlg = MemberDialog(parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        ok, _, msg = add_member(
            usn=d["usn"], name=d["name"], department=d["department"],
            semester=d["semester"], membership_type=d["membership_type"],
            email=d["email"], phone=d["phone"],
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Registered", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _edit_selected(self):
        member_id = self._selected_member_id()
        if member_id is None:
            return
        member_data = get_member_by_id(member_id)
        if not member_data:
            QMessageBox.critical(self, "Error", f"Member ID {member_id} not found.")
            return
        dlg = MemberDialog(member_data=member_data, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        d = dlg.get_data()
        ok, _, msg = update_member(
            member_id=member_id, name=d["name"], department=d["department"],
            semester=d["semester"], membership_type=d["membership_type"],
            email=d["email"], phone=d["phone"], status=d["status"],
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Updated", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)

    def _delete_selected(self):
        member_id = self._selected_member_id()
        if member_id is None:
            return
        row = self.table.currentRow()
        name = self.table.item(row, 2).text() if self.table.item(row, 2) else f"Member #{member_id}"
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Permanently remove '{name}' from the member directory?\n\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        ok, msg = delete_member(member_id, processed_by=self.current_user.get("username", "admin"))
        if ok:
            QMessageBox.information(self, "Deleted", msg)
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Cannot Delete", msg)

    def _toggle_status(self):
        member_id = self._selected_member_id()
        if member_id is None:
            return
        member_data = get_member_by_id(member_id)
        if not member_data:
            return
        new_status = "Suspended" if member_data["status"] == "Active" else "Active"
        ok, _, msg = update_member(
            member_id=member_id, status=new_status,
            processed_by=self.current_user.get("username", "admin"),
        )
        if ok:
            QMessageBox.information(self, "Status Updated",
                                    f"Member '{member_data['name']}' is now {new_status}.")
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", msg)
