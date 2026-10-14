"""
Payroll Widget — Automated Staff Payroll Processing & Pay Slip Export.
Course: BBAT104 - Total Quality Management.
Demonstrates TQM Principle: Error Reduction, Standardized Calculations & Audit Compliance.
"""

from datetime import date, datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QSpinBox,
    QMessageBox,
    QFrame,
    QGridLayout,
)
from PySide6.QtCore import Qt
from services.payroll_service import (
    generate_all_staff_payrolls,
    get_all_payrolls,
    update_payroll_status,
)
from services.report_service import generate_payslip_pdf, generate_quality_audit_excel
from services.logger_service import get_logger

logger = get_logger("gui.payroll")


class PayrollWidget(QWidget):
    """
    Automated Monthly Payroll Engine & Pay Slip Generator.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header Row
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Automated Staff Payroll Engine")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("Automated shift aggregation, overtime multipliers, statutory deductions & ReportLab PDF pay slips")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        # Month / Year Selectors
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(datetime(2000, m, 1).strftime("%B"), m)
        self.month_combo.setCurrentIndex(date.today().month - 1)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2035)
        self.year_spin.setValue(date.today().year)

        self.calc_btn = QPushButton("⚡ Automate Payroll Calculation")
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 700;
                padding: 9px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.calc_btn.clicked.connect(self._run_automated_payroll)

        header.addWidget(QLabel("Period:"))
        header.addWidget(self.month_combo)
        header.addWidget(self.year_spin)
        header.addWidget(self.calc_btn)
        layout.addLayout(header)

        # Summary Metric Cards Row
        summary_grid = QGridLayout()
        summary_grid.setSpacing(12)

        self.card_gross = self._create_mini_card("Total Gross Payroll", "Rs. 0.00", "#2563EB")
        self.card_net = self._create_mini_card("Total Net Salary", "Rs. 0.00", "#10B981")
        self.card_deductions = self._create_mini_card("Total Statutory Deductions", "Rs. 0.00", "#EF4444")
        self.card_ot = self._create_mini_card("Total Overtime Hours", "0.0 hrs", "#F59E0B")

        summary_grid.addWidget(self.card_gross, 0, 0)
        summary_grid.addWidget(self.card_net, 0, 1)
        summary_grid.addWidget(self.card_deductions, 0, 2)
        summary_grid.addWidget(self.card_ot, 0, 3)
        layout.addLayout(summary_grid)

        # Action Toolbar & Table
        action_row = QHBoxLayout()
        table_label = QLabel("Staff Payroll Disbursal Ledger")
        table_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")
        action_row.addWidget(table_label)
        action_row.addStretch()

        self.export_excel_btn = QPushButton("📊 Export Quality Audit Excel")
        self.export_excel_btn.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 6px 14px; border-radius: 6px; font-weight: 600;")
        self.export_excel_btn.clicked.connect(self._export_excel_audit)
        action_row.addWidget(self.export_excel_btn)
        layout.addLayout(action_row)

        # Payroll Table
        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(10)
        self.payroll_table.setHorizontalHeaderLabels([
            "ID", "Staff Full Name", "Role", "Period", "Regular Hours", "OT Hours",
            "Gross Pay (INR)", "Deductions (5%)", "Net Salary (INR)", "Status"
        ])
        self.payroll_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payroll_table.verticalHeader().setVisible(False)
        self.payroll_table.setAlternatingRowColors(True)
        layout.addWidget(self.payroll_table)

        # Bottom Actions Bar
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.generate_pdf_btn = QPushButton("📄 Generate Selected Staff PDF Pay Slip")
        self.generate_pdf_btn.setStyleSheet("background-color: #0F172A; color: #FFFFFF; font-weight: 600; padding: 8px 18px; border-radius: 6px;")
        self.generate_pdf_btn.clicked.connect(self._generate_selected_pdf)

        self.approve_btn = QPushButton("✓ Mark Payroll Approved")
        self.approve_btn.setStyleSheet("background-color: #10B981; color: #FFFFFF; font-weight: 600; padding: 8px 18px; border-radius: 6px;")
        self.approve_btn.clicked.connect(self._approve_selected_payroll)

        bottom_row.addWidget(self.generate_pdf_btn)
        bottom_row.addWidget(self.approve_btn)
        layout.addLayout(bottom_row)

    def _create_mini_card(self, title: str, value: str, accent: str) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        card.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-left: 4px solid {accent};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(10, 8, 10, 8)
        c_layout.setSpacing(2)

        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 700;")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("valueLabel")
        v_lbl.setStyleSheet("color: #0F172A; font-size: 20px; font-weight: 800;")

        c_layout.addWidget(t_lbl)
        c_layout.addWidget(v_lbl)
        return card

    def refresh_data(self):
        """Loads all payroll records and updates summary cards."""
        payrolls = get_all_payrolls()
        self.payroll_table.setRowCount(len(payrolls))

        total_gross = sum(p["gross_salary"] for p in payrolls)
        total_net = sum(p["net_salary"] for p in payrolls)
        total_ded = sum(p["deductions"] for p in payrolls)
        total_ot = sum(p["total_overtime_hours"] for p in payrolls)

        # Update cards
        self.card_gross.findChild(QLabel, "valueLabel").setText(f"Rs. {total_gross:,.2f}")
        self.card_net.findChild(QLabel, "valueLabel").setText(f"Rs. {total_net:,.2f}")
        self.card_deductions.findChild(QLabel, "valueLabel").setText(f"Rs. {total_ded:,.2f}")
        self.card_ot.findChild(QLabel, "valueLabel").setText(f"{total_ot:.1f} hrs")

        for row, p in enumerate(payrolls):
            self.payroll_table.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self.payroll_table.setItem(row, 1, QTableWidgetItem(p["staff_name"]))
            self.payroll_table.setItem(row, 2, QTableWidgetItem(p["role"]))
            self.payroll_table.setItem(row, 3, QTableWidgetItem(p["period"]))
            self.payroll_table.setItem(row, 4, QTableWidgetItem(f"{p['total_regular_hours']:.1f}"))
            self.payroll_table.setItem(row, 5, QTableWidgetItem(f"{p['total_overtime_hours']:.1f}"))
            self.payroll_table.setItem(row, 6, QTableWidgetItem(f"Rs. {p['gross_salary']:,.2f}"))
            self.payroll_table.setItem(row, 7, QTableWidgetItem(f"Rs. {p['deductions']:,.2f}"))
            self.payroll_table.setItem(row, 8, QTableWidgetItem(f"Rs. {p['net_salary']:,.2f}"))

            status_item = QTableWidgetItem(p["status"])
            if p["status"] == "Approved":
                status_item.setForeground(Qt.darkGreen)
            elif p["status"] == "Processed":
                status_item.setForeground(Qt.darkBlue)
            self.payroll_table.setItem(row, 9, status_item)

    def _run_automated_payroll(self):
        month = self.month_combo.currentData()
        year = self.year_spin.value()

        count, records = generate_all_staff_payrolls(month, year)
        self.refresh_data()
        QMessageBox.information(
            self,
            "TQM Automated Payroll",
            f"Automated payroll processed successfully for {count} staff members ({datetime(year, month, 1).strftime('%B %Y')}).",
        )

    def _get_selected_row(self) -> int:
        selected = self.payroll_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selection Required", "Please select a staff payroll record from the table.")
            return -1
        return selected

    def _generate_selected_pdf(self):
        row = self._get_selected_row()
        if row < 0:
            return

        name = self.payroll_table.item(row, 1).text()
        role = self.payroll_table.item(row, 2).text()
        period = self.payroll_table.item(row, 3).text()
        reg_hours = float(self.payroll_table.item(row, 4).text())
        ot_hours = float(self.payroll_table.item(row, 5).text())

        # Clean gross and net strings
        gross = float(self.payroll_table.item(row, 6).text().replace("Rs.", "").replace(",", "").strip())
        ded = float(self.payroll_table.item(row, 7).text().replace("Rs.", "").replace(",", "").strip())
        net = float(self.payroll_table.item(row, 8).text().replace("Rs.", "").replace(",", "").strip())

        try:
            pdf_path = generate_payslip_pdf(
                staff_name=name,
                period=period,
                gross=gross,
                deductions=ded,
                net=net,
                regular_hours=reg_hours,
                overtime_hours=ot_hours,
                hourly_rate=120.0,
                role=role,
            )
            QMessageBox.information(
                self,
                "PDF Pay Slip Generated",
                f"Official executive pay slip PDF generated successfully:\n\n{pdf_path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to generate pay slip PDF: {exc}")

    def _approve_selected_payroll(self):
        row = self._get_selected_row()
        if row < 0:
            return

        payroll_id = int(self.payroll_table.item(row, 0).text())
        update_payroll_status(payroll_id, "Approved")
        self.refresh_data()
        QMessageBox.information(self, "Status Updated", f"Payroll #{payroll_id} status changed to 'Approved'.")

    def _export_excel_audit(self):
        try:
            path = generate_quality_audit_excel()
            QMessageBox.information(
                self,
                "Excel Export Complete",
                f"TQM Quality Audit ledger exported successfully to Excel:\n\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", f"Failed to export Excel audit: {exc}")
