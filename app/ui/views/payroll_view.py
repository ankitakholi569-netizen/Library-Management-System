"""
Payroll View — Staff Operational Shifts & Automated Payroll Calculation Engine.
Demonstrates TQM Principle: Process Automation, Error Reduction & Standardized Computation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QDoubleSpinBox, QDateEdit, QLineEdit,
    QMessageBox, QFrame, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from datetime import date
from app.models.base import get_db
from app.models.user import User
from app.models.payroll import StaffShift, StaffPayroll
from app.services.payroll_service import log_shift, generate_payroll
from app.services.report_service import generate_payslip_pdf
from app.core.logger import get_logger

logger = get_logger("ui.payroll")


class LogShiftDialog(QDialog):
    """Dialog to record a daily staff shift."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Staff Shift")
        self.setFixedWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()

        self.staff_combo = QComboBox()
        with get_db() as db:
            staff_list = db.query(User).filter(User.is_active == True).all()
            for s in staff_list:
                self.staff_combo.addItem(f"{s.full_name} ({s.role})", s.id)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())

        self.reg_hours = QDoubleSpinBox()
        self.reg_hours.setRange(0.0, 16.0)
        self.reg_hours.setValue(8.0)
        self.reg_hours.setSingleStep(0.5)

        self.ot_hours = QDoubleSpinBox()
        self.ot_hours.setRange(0.0, 12.0)
        self.ot_hours.setValue(0.0)
        self.ot_hours.setSingleStep(0.5)

        self.tasks_input = QLineEdit("Cataloging and circulation desk duty")

        form.addRow("Staff Member *:", self.staff_combo)
        form.addRow("Shift Date *:", self.date_picker)
        form.addRow("Regular Hours *:", self.reg_hours)
        form.addRow("Overtime Hours:", self.ot_hours)
        form.addRow("Tasks Summary:", self.tasks_input)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Record Shift")
        save_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 6px 14px;")
        save_btn.clicked.connect(self._save_shift)

        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save_shift(self):
        user_id = self.staff_combo.currentData()
        qdate = self.date_picker.date()
        shift_date = date(qdate.year(), qdate.month(), qdate.day())
        reg = self.reg_hours.value()
        ot = self.ot_hours.value()
        tasks = self.tasks_input.text().strip()

        res = log_shift(user_id, shift_date, reg, ot, tasks)
        if res["success"]:
            QMessageBox.information(self, "Shift Recorded", res["message"])
            self.accept()
        else:
            QMessageBox.warning(self, "Error", res["message"])


class PayrollView(QWidget):
    """Staff attendance shifts and automated salary calculation dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        t = QLabel("Staff Management & Automated Payroll Engine")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        st = QLabel("Shift aggregation, automated overtime calculation (1.5x) & PDF pay slips")
        st.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(t)
        title_box.addWidget(st)
        header.addLayout(title_box)
        header.addStretch()

        self.log_shift_btn = QPushButton("+ Record Shift")
        self.log_shift_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: 600; padding: 8px 14px;")
        self.log_shift_btn.clicked.connect(self._open_shift_dialog)
        header.addWidget(self.log_shift_btn)

        self.gen_payroll_btn = QPushButton("⚡ Generate Month Payroll")
        self.gen_payroll_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 14px;")
        self.gen_payroll_btn.clicked.connect(self._generate_payroll)
        header.addWidget(self.gen_payroll_btn)

        layout.addLayout(header)

        # Tabs for Payroll History and Shift Logs
        self.tabs = QTabWidget()

        # Tab 1: Payroll Summaries
        payroll_tab = QWidget()
        p_layout = QVBoxLayout(payroll_tab)
        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(8)
        self.payroll_table.setHorizontalHeaderLabels([
            "Staff Member", "Period", "Regular Hrs", "OT Hrs", "Gross (Rs.)", "Deductions (Rs.)", "Net Salary (Rs.)", "Pay Slip"
        ])
        self.payroll_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.payroll_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payroll_table.setEditTriggers(QTableWidget.NoEditTriggers)
        p_layout.addWidget(self.payroll_table)
        self.tabs.addTab(payroll_tab, "Automated Payroll Records")

        # Tab 2: Shift Logs
        shift_tab = QWidget()
        s_layout = QVBoxLayout(shift_tab)
        self.shift_table = QTableWidget()
        self.shift_table.setColumnCount(6)
        self.shift_table.setHorizontalHeaderLabels([
            "Staff Name", "Date", "Shift Type", "Regular Hrs", "OT Hrs", "Tasks Summary"
        ])
        self.shift_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.shift_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.shift_table.setEditTriggers(QTableWidget.NoEditTriggers)
        s_layout.addWidget(self.shift_table)
        self.tabs.addTab(shift_tab, "Recent Staff Shifts")

        layout.addWidget(self.tabs)

    def load_data(self):
        self._load_payroll()
        self._load_shifts()

    def _load_payroll(self):
        with get_db() as db:
            from sqlalchemy.orm import joinedload
            payrolls = db.query(StaffPayroll).options(joinedload(StaffPayroll.user)).order_by(StaffPayroll.id.desc()).all()
            self.payroll_table.setRowCount(len(payrolls))
            for row, p in enumerate(payrolls):
                staff_name = p.user.full_name if p.user else "N/A"
                period = f"{p.period_month:02d}/{p.period_year}"
                self.payroll_table.setItem(row, 0, QTableWidgetItem(staff_name))
                self.payroll_table.setItem(row, 1, QTableWidgetItem(period))
                self.payroll_table.setItem(row, 2, QTableWidgetItem(f"{p.total_regular_hours:.1f}"))
                self.payroll_table.setItem(row, 3, QTableWidgetItem(f"{p.total_overtime_hours:.1f}"))
                self.payroll_table.setItem(row, 4, QTableWidgetItem(f"Rs. {p.gross_salary:.2f}"))
                self.payroll_table.setItem(row, 5, QTableWidgetItem(f"Rs. {p.deductions:.2f}"))

                net_item = QTableWidgetItem(f"Rs. {p.net_salary:.2f}")
                net_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.payroll_table.setItem(row, 6, net_item)

                pdf_btn = QPushButton("Download PDF")
                pdf_btn.setStyleSheet("background-color: #0284C7; color: white; padding: 4px 8px; font-size: 11px;")
                pdf_btn.clicked.connect(lambda _, item=p: self._download_pdf(item))
                self.payroll_table.setCellWidget(row, 7, pdf_btn)

    def _load_shifts(self):
        with get_db() as db:
            from sqlalchemy.orm import joinedload
            shifts = db.query(StaffShift).options(joinedload(StaffShift.user)).order_by(StaffShift.shift_date.desc()).limit(100).all()
            self.shift_table.setRowCount(len(shifts))
            for row, s in enumerate(shifts):
                staff_name = s.user.full_name if s.user else "N/A"
                self.shift_table.setItem(row, 0, QTableWidgetItem(staff_name))
                self.shift_table.setItem(row, 1, QTableWidgetItem(str(s.shift_date)))
                self.shift_table.setItem(row, 2, QTableWidgetItem(s.shift_type))
                self.shift_table.setItem(row, 3, QTableWidgetItem(f"{s.regular_hours:.1f}"))
                self.shift_table.setItem(row, 4, QTableWidgetItem(f"{s.overtime_hours:.1f}"))
                self.shift_table.setItem(row, 5, QTableWidgetItem(s.tasks_completed))

    def _open_shift_dialog(self):
        dlg = LogShiftDialog(parent=self)
        if dlg.exec():
            self.load_data()

    def _generate_payroll(self):
        with get_db() as db:
            users = db.query(User).filter(User.is_active == True).all()

        today = date.today()
        count = 0
        messages = []
        for u in users:
            res = generate_payroll(u.id, month=today.month, year=today.year)
            if res["success"]:
                count += 1
                messages.append(f"✓ {res['message']}")

        if count > 0:
            QMessageBox.information(
                self, "Payroll Complete",
                f"Generated automated payroll for {count} staff members:\n\n" + "\n".join(messages)
            )
            self.load_data()
        else:
            QMessageBox.information(
                self, "Already Processed",
                f"All active staff members already have payroll generated for {today.month:02d}/{today.year}."
            )

    def _download_pdf(self, payroll: StaffPayroll):
        try:
            with get_db() as db:
                p = db.get(StaffPayroll, payroll.id)
                staff_name = p.user.full_name if p.user else "Staff"
                hourly_rate = p.user.hourly_rate if p.user else 150.0

                filepath = generate_payslip_pdf(
                    staff_name=staff_name,
                    period=f"{p.period_month:02d}/{p.period_year}",
                    gross=p.gross_salary,
                    deductions=p.deductions,
                    net=p.net_salary,
                    regular_hours=p.total_regular_hours,
                    overtime_hours=p.total_overtime_hours,
                    hourly_rate=hourly_rate,
                )
            QMessageBox.information(self, "Pay Slip Created", f"PDF Pay Slip generated successfully:\n\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Export Failed", f"Could not generate PDF pay slip: {e}")
