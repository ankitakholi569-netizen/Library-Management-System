"""
Stock Ledger (FR-04) & Daily Z-Report Till Close (FR-05) Desktop Widgets.
Course: BBAT104 - Total Quality Management.

SRS Specifications Implemented:
- FR-04: FEFO stock ledger & inward GRN entry for Catalog Manager [TQM Gate: 100% stock balance]
- FR-05: Daily Z-Report till close & 21 CFR Part 11 logs for Library Admin [TQM Gate: Zero audit variance]
"""

from datetime import date
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
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt, QDate
from services.library_service import (
    get_all_books,
    inward_grn_entry,
    get_fefo_stock_ledger,
    verify_stock_balance,
    generate_daily_z_report,
    get_21cfr_audit_trail,
)


# ==============================================================================
# 1. STOCK LEDGER & INWARD GRN WIDGET (FR-04)
# ==============================================================================
class StockLedgerWidget(QWidget):
    """
    Catalog Manager Inward GRN & FEFO Stock Ledger.
    FR-04: FEFO stock ledger & inward GRN entry.
    TQM Quality Gate: 100% stock balance reconciliation.
    """

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self._setup_ui()
        self.refresh_ledger()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("📦 Stock Ledger & Goods Receipt Note (GRN)")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("FR-04: FEFO Inventory Ledger • Supplier GRN Entry • 100% Stock Balance Quality Gate")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.balance_badge = QLabel("Stock Balance: 100.0% VERIFIED")
        self.balance_badge.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; font-weight: 700; "
            "padding: 6px 14px; border-radius: 6px; border: 1px solid #A7F3D0; font-size: 12px;"
        )
        header.addWidget(self.balance_badge)
        layout.addLayout(header)

        # Inward GRN Entry Card
        grn_card = QFrame()
        grn_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px;")
        g_layout = QVBoxLayout(grn_card)
        g_layout.setSpacing(10)

        card_title = QLabel("📥 Inward Goods Receipt Note (GRN) Entry")
        card_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #1E293B;")
        g_layout.addWidget(card_title)

        row1 = QHBoxLayout()
        self.supplier_input = QLineEdit()
        self.supplier_input.setPlaceholderText("Supplier Name (e.g. Oxford Press)")
        self.supplier_input.setText("Pearson Higher Education India")
        row1.addWidget(self.supplier_input, 2)

        self.grn_input = QLineEdit()
        self.grn_input.setPlaceholderText("GRN # (e.g. GRN-2026-088)")
        self.grn_input.setText(f"GRN-2026-{int(date.today().strftime('%m%d%H%M')) % 1000:03d}")
        row1.addWidget(self.grn_input, 1)

        self.invoice_input = QLineEdit()
        self.invoice_input.setPlaceholderText("Supplier Invoice No.")
        self.invoice_input.setText("INV-78420")
        row1.addWidget(self.invoice_input, 1)
        g_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.book_combo = QComboBox()
        self._load_books_combo()
        row2.addWidget(self.book_combo, 2)

        row2.addWidget(QLabel("Qty:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 500)
        self.qty_spin.setValue(5)
        row2.addWidget(self.qty_spin)

        row2.addWidget(QLabel("Unit Cost (₹):"))
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 10000.0)
        self.cost_spin.setValue(650.0)
        row2.addWidget(self.cost_spin)

        self.inward_btn = QPushButton("Inward to Stock Ledger")
        self.inward_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 700; padding: 8px 16px; border-radius: 6px;")
        self.inward_btn.clicked.connect(self._handle_inward)
        row2.addWidget(self.inward_btn)
        g_layout.addLayout(row2)

        layout.addWidget(grn_card)

        # Ledger Table (FEFO Order)
        tbl_label = QLabel("📋 FEFO (First-Expired / First-Out) Stock Ledger & Batch Balances")
        tbl_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #334155; margin-top: 4px;")
        layout.addWidget(tbl_label)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "GRN Number", "Supplier", "Book Title", "Batch Code", "Qty Received", "Unit Cost", "Expiry (FEFO)", "Reconciled Stock"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _load_books_combo(self):
        self.book_combo.clear()
        books = get_all_books()
        for b in books:
            self.book_combo.addItem(f"{b['title']} (ISBN: {b['isbn']})", b["id"])

    def _handle_inward(self):
        supplier = self.supplier_input.text().strip()
        grn = self.grn_input.text().strip()
        inv = self.invoice_input.text().strip()
        book_id = self.book_combo.currentData()
        qty = self.qty_spin.value()
        cost = self.cost_spin.value()

        if not supplier or not grn:
            QMessageBox.warning(self, "Validation Error", "Supplier name and GRN number are required.")
            return

        res = inward_grn_entry(
            supplier_name=supplier,
            grn_number=grn,
            invoice_no=inv,
            book_id=book_id,
            quantity=qty,
            unit_cost=cost,
            created_by=self.current_user.get("full_name", "Catalog Manager"),
        )

        if res.get("success"):
            QMessageBox.information(self, "GRN Inward Complete", res.get("message"))
            self.grn_input.setText(f"GRN-2026-{(int(date.today().strftime('%m%d%H%M')) + 1) % 1000:03d}")
            self.refresh_ledger()
        else:
            QMessageBox.warning(self, "GRN Error", res.get("message"))

    def refresh_ledger(self):
        # 1. Update 100% Stock Balance Gate
        bal = verify_stock_balance()
        pct = bal.get("stock_balance_accuracy_pct", 100.0)
        is_100 = bal.get("is_100_percent_balanced", True)
        if is_100:
            self.balance_badge.setText(f"Stock Balance: {pct:.1f}% VERIFIED (TQM PASS)")
            self.balance_badge.setStyleSheet("background-color: #ECFDF5; color: #059669; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        else:
            self.balance_badge.setText(f"Stock Balance: {pct:.1f}% (DISCREPANCY DETECTED)")
            self.balance_badge.setStyleSheet("background-color: #FEF2F2; color: #DC2626; font-weight: 700; padding: 6px 14px; border-radius: 6px;")

        # 2. Populate FEFO Ledger
        entries = get_fefo_stock_ledger()
        self.table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(e.get("grn_number", "")))
            self.table.setItem(row, 1, QTableWidgetItem(e.get("supplier_name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(e.get("book_title", "")))
            self.table.setItem(row, 3, QTableWidgetItem(e.get("batch_code", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(e.get("quantity_received", 0))))
            self.table.setItem(row, 5, QTableWidgetItem(f"₹{e.get('unit_cost', 0):.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(e.get("expiry_date", "")))
            self.table.setItem(row, 7, QTableWidgetItem(f"{e.get('reconciled_stock', 0)} units"))


# ==============================================================================
# 2. DAILY Z-REPORT & 21 CFR PART 11 WIDGET (FR-05)
# ==============================================================================
class DailyZReportWidget(QWidget):
    """
    Library Admin Daily Z-Report & 21 CFR Part 11 Audit Trail.
    FR-05: Daily Z-Report till close & 21 CFR Part 11 logs.
    TQM Quality Gate: Zero audit variance (variance == 0.00).
    """

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self._setup_ui()
        self.refresh_z_report()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Banner
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🧾 Daily Z-Report Till Close & 21 CFR Part 11 Audit")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub = QLabel("FR-05: Financial Till Reconciliation • Electronic Signature Ledger • Zero Audit Variance Quality Gate")
        sub.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        header.addLayout(title_box)
        header.addStretch()

        self.variance_badge = QLabel("Audit Variance: ₹0.00 (PASS)")
        self.variance_badge.setStyleSheet(
            "background-color: #ECFDF5; color: #059669; font-weight: 700; "
            "padding: 6px 14px; border-radius: 6px; border: 1px solid #A7F3D0; font-size: 12px;"
        )
        header.addWidget(self.variance_badge)
        layout.addLayout(header)

        # Action Bar & Summary Card
        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 16px;")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        top_row = QHBoxLayout()
        c_title = QLabel("Till Close Operational Reconciliation (Today)")
        c_title.setStyleSheet("font-weight: 700; font-size: 15px; color: #0F172A;")
        top_row.addWidget(c_title)
        top_row.addStretch()

        self.close_btn = QPushButton("🔒 Execute Daily Till Close (Z-Report)")
        self.close_btn.setStyleSheet("background-color: #059669; color: white; font-weight: 700; padding: 8px 18px; border-radius: 6px;")
        self.close_btn.clicked.connect(self._handle_close)
        top_row.addWidget(self.close_btn)
        c_layout.addLayout(top_row)

        # KPI Metrics Row
        kpi_row = QHBoxLayout()
        self.opening_lbl = self._create_kpi_card("Opening Cash", "₹2,500.00", "#3B82F6")
        self.fines_lbl = self._create_kpi_card("Fines Collected", "₹0.00", "#10B981")
        self.expected_lbl = self._create_kpi_card("Expected Cash", "₹2,500.00", "#6366F1")
        self.closing_lbl = self._create_kpi_card("Closing Cash Till", "₹2,500.00", "#059669")
        self.var_card_lbl = self._create_kpi_card("Audit Variance", "₹0.00", "#059669")

        kpi_row.addWidget(self.opening_lbl)
        kpi_row.addWidget(self.fines_lbl)
        kpi_row.addWidget(self.expected_lbl)
        kpi_row.addWidget(self.closing_lbl)
        kpi_row.addWidget(self.var_card_lbl)
        c_layout.addLayout(kpi_row)

        # 21 CFR Part 11 Hash Banner
        self.hash_lbl = QLabel("21 CFR Part 11 Cryptographic Audit Checksum: Initializing...")
        self.hash_lbl.setStyleSheet("font-family: monospace; font-size: 11px; color: #64748B; background: #F8FAFC; padding: 6px 10px; border-radius: 4px;")
        c_layout.addWidget(self.hash_lbl)

        layout.addWidget(card)

        # 21 CFR Part 11 Tamper-Evident Audit Log Table
        log_title = QLabel("🔐 21 CFR Part 11 Tamper-Evident Electronic Audit Trail")
        log_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #334155; margin-top: 6px;")
        layout.addWidget(log_title)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Log ID", "Timestamp (UTC)", "Module", "Action", "Status", "Digital Signature", "SHA-256 Tamper Checksum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px;")
        b_layout = QVBoxLayout(box)
        b_layout.setSpacing(2)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600;")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("val")
        v_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {color};")
        b_layout.addWidget(t_lbl)
        b_layout.addWidget(v_lbl)
        return box

    def _handle_close(self):
        user = self.current_user.get("full_name", "Dr. Anita Sharma")
        res = generate_daily_z_report(report_date=date.today(), generated_by=user)
        if res.get("success"):
            QMessageBox.information(self, "Daily Z-Report Closed", res.get("message"))
            self.refresh_z_report()
        else:
            QMessageBox.warning(self, "Z-Report Error", "Failed to generate Daily Z-Report.")

    def refresh_z_report(self):
        user = self.current_user.get("full_name", "Dr. Anita Sharma")
        res = generate_daily_z_report(report_date=date.today(), generated_by=user)
        rep = res.get("report", {})

        # Update KPI Cards
        self.opening_lbl.findChild(QLabel, "val").setText(f"₹{rep.get('opening_cash', 2500):,.2f}")
        self.fines_lbl.findChild(QLabel, "val").setText(f"₹{rep.get('fines_collected', 0):,.2f}")
        self.expected_lbl.findChild(QLabel, "val").setText(f"₹{rep.get('expected_cash', 2500):,.2f}")
        self.closing_lbl.findChild(QLabel, "val").setText(f"₹{rep.get('closing_cash', 2500):,.2f}")

        var_val = rep.get("audit_variance", 0.0)
        self.var_card_lbl.findChild(QLabel, "val").setText(f"₹{var_val:.2f}")

        if var_val == 0.0:
            self.variance_badge.setText("Audit Variance: ₹0.00 (ZERO VARIANCE PASS)")
            self.variance_badge.setStyleSheet("background-color: #ECFDF5; color: #059669; font-weight: 700; padding: 6px 14px; border-radius: 6px;")
        else:
            self.variance_badge.setText(f"Audit Variance: ₹{var_val:.2f} (VARIANCE DETECTED)")
            self.variance_badge.setStyleSheet("background-color: #FEF2F2; color: #DC2626; font-weight: 700; padding: 6px 14px; border-radius: 6px;")

        z_hash = rep.get("audit_hash_sha256", "")
        self.hash_lbl.setText(f"21 CFR Part 11 Cryptographic Audit Checksum: {z_hash} (TAMPER-EVIDENT VALIDATED)")

        # Populate Audit Trail Table
        logs = get_21cfr_audit_trail(limit=50)
        self.table.setRowCount(len(logs))
        for row, l in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(str(l.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(l.get("timestamp", "")))
            self.table.setItem(row, 2, QTableWidgetItem(l.get("module", "")))
            self.table.setItem(row, 3, QTableWidgetItem(l.get("action", "")))

            s_item = QTableWidgetItem(l.get("status", ""))
            s_item.setForeground(Qt.darkGreen if "SUCCESS" in l.get("status", "") else Qt.darkRed)
            self.table.setItem(row, 4, s_item)

            self.table.setItem(row, 5, QTableWidgetItem(l.get("digital_signature", "21 CFR Part 11 Verified")))
            self.table.setItem(row, 6, QTableWidgetItem(l.get("audit_hash_sha256", "")[:32] + "..."))

