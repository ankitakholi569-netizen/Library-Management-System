"""
Quality Audit View — TQM Quality Monitoring, Continuous Improvement & SLA Ledger.
Demonstrates TQM Principle: Quality Monitoring, Audit Trails & Continuous Improvement.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from app.models.base import get_db
from app.models.quality_log import QualityLog
from app.ui.components.kpi_badge import KPIBadge
from app.ui.components.stat_card import StatCard
from app.core.logger import get_logger

logger = get_logger("ui.quality")


class QualityAuditView(QWidget):
    """Real-time ledger of all system transactions, SLA adherence, and query latencies."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_audit_logs()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        t = QLabel("TQM Continuous Improvement & Quality Audit Log")
        t.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        st = QLabel("Audits transaction latency, SLA breaches, security operations & defect resolutions")
        st.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(t)
        title_box.addWidget(st)
        header.addLayout(title_box)
        header.addStretch()

        self.refresh_btn = QPushButton("Refresh Audit Trail")
        self.refresh_btn.setStyleSheet("background-color: #2563EB; color: white; font-weight: 600; padding: 8px 14px;")
        self.refresh_btn.clicked.connect(self.load_audit_logs)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Audit Summary KPI Cards
        card_row = QHBoxLayout()
        self.card_total = StatCard("Total Audit Records", "0", "Monitored Transactions", "#2563EB")
        self.card_avg_time = StatCard("Avg Execution Latency", "0 ms", "Performance SLA", "#10B981")
        self.card_breaches = StatCard("SLA Defect Alerts", "0", "Continuous Improvement", "#EF4444")
        card_row.addWidget(self.card_total)
        card_row.addWidget(self.card_avg_time)
        card_row.addWidget(self.card_breaches)
        layout.addLayout(card_row)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Filter Module:"))
        self.module_filter = QComboBox()
        self.module_filter.addItems(["All Modules", "CIRCULATION", "CATALOG", "PAYROLL", "SECURITY", "SYSTEM"])
        self.module_filter.currentTextChanged.connect(self._filter_logs)
        filter_bar.addWidget(self.module_filter)

        filter_bar.addWidget(QLabel("Filter Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "SUCCESS", "SLA_BREACH", "WARNING", "ERROR"])
        self.status_filter.currentTextChanged.connect(self._filter_logs)
        filter_bar.addWidget(self.status_filter)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Audit Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Module", "Action", "Status", "Latency (ms)", "Audit Details & SLA Notes"
        ])
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_audit_logs(self):
        with get_db() as db:
            self.logs = db.query(QualityLog).order_by(QualityLog.timestamp.desc()).limit(200).all()

        total = len(self.logs)
        latencies = [l.execution_time_ms for l in self.logs if l.execution_time_ms is not None]
        avg_lat = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
        breaches = sum(1 for l in self.logs if l.status in ["SLA_BREACH", "ERROR"])

        self.card_total.update_value(str(total))
        self.card_avg_time.update_value(f"{avg_lat} ms")
        self.card_breaches.update_value(str(breaches))

        self._filter_logs()

    def _filter_logs(self):
        mod = self.module_filter.currentText()
        stat = self.status_filter.currentText()

        filtered = []
        for l in self.logs:
            if mod != "All Modules" and l.module != mod:
                continue
            if stat != "All Statuses" and l.status != stat:
                continue
            filtered.append(l)

        self.table.setRowCount(len(filtered))
        for row, l in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else ""))
            self.table.setItem(row, 1, QTableWidgetItem(l.module))
            self.table.setItem(row, 2, QTableWidgetItem(l.action))

            # Status Badge
            scheme = "success" if l.status == "SUCCESS" else ("danger" if l.status in ["SLA_BREACH", "ERROR"] else "warning")
            self.table.setCellWidget(row, 3, KPIBadge(l.status, scheme))

            lat_str = f"{l.execution_time_ms:.1f} ms" if l.execution_time_ms is not None else "-"
            lat_item = QTableWidgetItem(lat_str)
            lat_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, lat_item)

            self.table.setItem(row, 5, QTableWidgetItem(l.details or ""))
