"""
Employee & Shift Management Widget.
Course: BBAT104 - Total Quality Management.
Features:
- Staff roster with role, department, and hourly rate tracking
- Shift attendance logger with overtime hour tracking
- Operational performance records
"""

from datetime import date
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QDialog,
    QFormLayout,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QMessageBox,
    QFrame,
    QTabWidget,
)
from PySide6.QtCore import Qt, QDate
from services.auth_service import get_all_users, get_staff_users, create_user
from services.payroll_service import log_shift, get_staff_shifts
from services.logger_service import get_logger

logger = get_logger("gui.employee")


class AddStaffDialog(QDialog):
    """Dialog to register a new staff user."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Library Staff")
        self.setFixedWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()

        self.username_input = QLineEdit()
        self.name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Assistant Librarian", "Library Assistant", "Chief Librarian"])

        self.dept_input = QLineEdit("Library Administration")

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(50.0, 1000.0)
        self.rate_input.setValue(120.0)
        self.rate_input.setPrefix("Rs. ")

        self.salary_input = QDoubleSpinBox()
        self.salary_input.setRange(10000.0, 200000.0)
        self.salary_input.setValue(24000.0)
        self.salary_input.setPrefix("Rs. ")

        form.addRow("Username *:", self.username_input)
        form.addRow("Full Name *:", self.name_input)
        form.addRow("Password *:", self.password_input)
        form.addRow("Designation *:", self.role_combo)
        form.addRow("Department:", self.dept_input)
        form.addRow("Hourly Rate (INR):", self.rate_input)
        form.addRow("Base Salary (INR):", self.salary_input)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Register Staff")
        save_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 7px 16px; border-radius: 6px;")
        save_btn.clicked.connect(self._handle_save)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _handle_save(self):
        username = self.username_input.text().strip()
        full_name = self.name_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not full_name or not password:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields.")
            return

        ok, user_data, msg = create_user(
            username=username,
            password=password,
            full_name=full_name,
            role=self.role_combo.currentText(),
            department=self.dept_input.text().strip(),
            hourly_rate=self.rate_input.value(),
            base_salary=self.salary_input.value(),
        )

        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return

        QMessageBox.information(self, "Success", f"Staff '{full_name}' registered successfully.")
        self.accept()


class LogShiftDialog(QDialog):
    """Dialog to record daily work shift for automated payroll computation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Staff Operational Shift")
        self.setFixedWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()

        self.staff_combo = QComboBox()
        staff_users = get_staff_users()
        for s in staff_users:
            self.staff_combo.addItem(f"{s['full_name']} ({s['role']})", s["id"])

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())

        self.shift_type_combo = QComboBox()
        self.shift_type_combo.addItems([
            "Regular Day Shift",
            "Desk Circulation Shift",
            "Catalog Stock Inspection",
            "Weekend Overtime Shift"
        ])

        self.reg_hours = QDoubleSpinBox()
        self.reg_hours.setRange(0.0, 16.0)
        self.reg_hours.setValue(8.0)
        self.reg_hours.setSingleStep(0.5)

        self.ot_hours = QDoubleSpinBox()
        self.ot_hours.setRange(0.0, 12.0)
        self.ot_hours.setValue(0.0)
        self.ot_hours.setSingleStep(0.5)

        self.tasks_input = QLineEdit("Catalog maintenance and desk circulation SLA monitoring")

        form.addRow("Staff Member *:", self.staff_combo)
        form.addRow("Shift Date *:", self.date_picker)
        form.addRow("Shift Classification:", self.shift_type_combo)
        form.addRow("Regular Hours:", self.reg_hours)
        form.addRow("Overtime Hours:", self.ot_hours)
        form.addRow("Tasks Summary:", self.tasks_input)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save Shift Record")
        save_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: 600; padding: 7px 16px; border-radius: 6px;")
        save_btn.clicked.connect(self._handle_save)

        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

    def _handle_save(self):
        user_id = self.staff_combo.currentData()
        if not user_id:
            QMessageBox.warning(self, "Validation Error", "No staff member selected.")
            return

        qdate = self.date_picker.date()
        shift_d = date(qdate.year(), qdate.month(), qdate.day())

        ok, shift_data, msg = log_shift(
            user_id=user_id,
            shift_date=shift_d,
            regular_hours=self.reg_hours.value(),
            overtime_hours=self.ot_hours.value(),
            shift_type=self.shift_type_combo.currentText(),
            tasks_completed=self.tasks_input.text().strip(),
            is_verified=True,
        )

        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return

        QMessageBox.information(self, "Success", "Shift record logged successfully.")
        self.accept()


class EmployeeWidget(QWidget):
    """
    Staff Roster & Operational Shift Logs Management View.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Staff Roster & Shift Performance Logs")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("Automated attendance logging, hourly compensation rates & performance tracking (TQM BBAT104)")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.add_staff_btn = QPushButton("+ Register Staff")
        self.add_staff_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 16px; border-radius: 6px;")
        self.add_staff_btn.clicked.connect(self._open_add_staff)

        self.log_shift_btn = QPushButton("⏱ Log Shift Attendance")
        self.log_shift_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: 600; padding: 8px 16px; border-radius: 6px;")
        self.log_shift_btn.clicked.connect(self._open_log_shift)

        header.addWidget(self.add_staff_btn)
        header.addWidget(self.log_shift_btn)
        layout.addLayout(header)

        # Tabs: Staff Directory vs Operational Shifts
        self.tabs = QTabWidget()

        # Tab 1: Staff Directory
        tab1_widget = QWidget()
        t1_layout = QVBoxLayout(tab1_widget)
        t1_layout.setContentsMargins(12, 12, 12, 12)

        # Search Bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Quick-Search Staff by Name, Username, or Department...")
        self.search_input.textChanged.connect(self._filter_staff_table)
        search_row.addWidget(self.search_input)
        t1_layout.addLayout(search_row)

        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(7)
        self.staff_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Designation", "Department", "Hourly Rate (INR)", "Status"
        ])
        self.staff_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setAlternatingRowColors(True)
        t1_layout.addWidget(self.staff_table)

        self.tabs.addTab(tab1_widget, "Staff Roster")

        # Tab 2: Operational Shift Logs
        tab2_widget = QWidget()
        t2_layout = QVBoxLayout(tab2_widget)
        t2_layout.setContentsMargins(12, 12, 12, 12)

        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(8)
        self.shifts_table.setHorizontalHeaderLabels([
            "Shift ID", "Staff Name", "Date", "Shift Type", "Regular Hours", "Overtime Hours", "Total Hours", "Status"
        ])
        self.shifts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.shifts_table.verticalHeader().setVisible(False)
        self.shifts_table.setAlternatingRowColors(True)
        t2_layout.addWidget(self.shifts_table)

        self.tabs.addTab(tab2_widget, "Operational Shift Logs")

        layout.addWidget(self.tabs)

    def refresh_data(self):
        """Loads staff directory and shift history."""
        self._load_staff_table()
        self._load_shifts_table()

    def _load_staff_table(self):
        self.staff_data = get_all_users()
        self.staff_table.setRowCount(len(self.staff_data))

        for row, u in enumerate(self.staff_data):
            self.staff_table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.staff_table.setItem(row, 1, QTableWidgetItem(u["username"]))
            self.staff_table.setItem(row, 2, QTableWidgetItem(u["full_name"]))
            self.staff_table.setItem(row, 3, QTableWidgetItem(u["role"]))
            self.staff_table.setItem(row, 4, QTableWidgetItem(u["department"]))
            self.staff_table.setItem(row, 5, QTableWidgetItem(f"Rs. {u['hourly_rate']:.2f}/hr"))

            status_item = QTableWidgetItem("Active" if u["is_active"] else "Inactive")
            status_item.setForeground(Qt.darkGreen if u["is_active"] else Qt.darkRed)
            self.staff_table.setItem(row, 6, status_item)

    def _load_shifts_table(self):
        shifts = get_staff_shifts()
        self.shifts_table.setRowCount(len(shifts))

        for row, s in enumerate(shifts):
            self.shifts_table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            self.shifts_table.setItem(row, 1, QTableWidgetItem(s["staff_name"]))
            self.shifts_table.setItem(row, 2, QTableWidgetItem(s["shift_date"]))
            self.shifts_table.setItem(row, 3, QTableWidgetItem(s["shift_type"]))
            self.shifts_table.setItem(row, 4, QTableWidgetItem(f"{s['regular_hours']:.1f} hrs"))
            self.shifts_table.setItem(row, 5, QTableWidgetItem(f"{s['overtime_hours']:.1f} hrs"))
            self.shifts_table.setItem(row, 6, QTableWidgetItem(f"{s['total_hours']:.1f} hrs"))

            verified_item = QTableWidgetItem("Verified" if s["is_verified"] else "Pending")
            verified_item.setForeground(Qt.darkGreen if s["is_verified"] else Qt.darkYellow)
            self.shifts_table.setItem(row, 7, verified_item)

    def _filter_staff_table(self, query: str):
        query = query.lower().strip()
        for row in range(self.staff_table.rowCount()):
            username = self.staff_table.item(row, 1).text().lower()
            name = self.staff_table.item(row, 2).text().lower()
            dept = self.staff_table.item(row, 4).text().lower()
            matches = (query in username) or (query in name) or (query in dept)
            self.staff_table.setRowHidden(row, not matches)

    def _open_add_staff(self):
        dlg = AddStaffDialog(self)
        if dlg.exec():
            self.refresh_data()

    def _open_log_shift(self):
        dlg = LogShiftDialog(self)
        if dlg.exec():
            self.refresh_data()
