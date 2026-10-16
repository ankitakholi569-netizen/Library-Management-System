"""
Dashboard View — Real-Time TQM Metrics & Embedded Matplotlib Charts.
Demonstrates TQM Principle: Data-Driven Decision Making & Visual Control.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.ui.components.stat_card import StatCard
from app.services.analytics_service import get_dashboard_kpis, get_department_wise_stats, get_loans_dataframe
from app.core.logger import get_logger

logger = get_logger("ui.dashboard")


class DashboardView(QWidget):
    """Executive TQM Analytics Dashboard with real-time KPI cards and visual charts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Row
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        page_title = QLabel("Executive TQM Dashboard")
        page_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        sub_title = QLabel("Real-Time Process Monitoring, Circulation SLA & Quality Compliance")
        sub_title.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(page_title)
        title_box.addWidget(sub_title)
        header_row.addLayout(title_box)

        header_row.addStretch()

        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setProperty("class", "primary-btn")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(self.refresh_btn)

        main_layout.addLayout(header_row)

        # KPI Cards Row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.card_books = StatCard("Total Books", "--", "Catalog Collection", "#2563EB")
        self.card_loans = StatCard("Active Loans", "--", "Circulation In-Flight", "#F59E0B")
        self.card_sla = StatCard("Return SLA", "--%", "Target: >= 90%", "#10B981")
        self.card_defect = StatCard("Catalog Defect Rate", "--%", "Tolerance: <= 2.0%", "#EF4444")

        kpi_row.addWidget(self.card_books)
        kpi_row.addWidget(self.card_loans)
        kpi_row.addWidget(self.card_sla)
        kpi_row.addWidget(self.card_defect)
        main_layout.addLayout(kpi_row)

        # Visual Analytics Section (Charts)
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Chart 1: Department Circulation
        chart1_card = QFrame()
        chart1_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;")
        chart1_layout = QVBoxLayout(chart1_card)
        chart1_layout.setContentsMargins(16, 14, 16, 14)
        lbl1 = QLabel("Loans by Academic Department")
        lbl1.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        chart1_layout.addWidget(lbl1)

        self.fig1 = Figure(figsize=(4.5, 3.2), dpi=100)
        self.fig1.patch.set_facecolor("#FFFFFF")
        self.canvas1 = FigureCanvas(self.fig1)
        chart1_layout.addWidget(self.canvas1)
        charts_row.addWidget(chart1_card)

        # Chart 2: Loan Status Breakdown
        chart2_card = QFrame()
        chart2_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;")
        chart2_layout = QVBoxLayout(chart2_card)
        chart2_layout.setContentsMargins(16, 14, 16, 14)
        lbl2 = QLabel("Circulation Loan Status Breakdown")
        lbl2.setStyleSheet("font-size: 14px; font-weight: 700; color: #1E293B;")
        chart2_layout.addWidget(lbl2)

        self.fig2 = Figure(figsize=(4.5, 3.2), dpi=100)
        self.fig2.patch.set_facecolor("#FFFFFF")
        self.canvas2 = FigureCanvas(self.fig2)
        chart2_layout.addWidget(self.canvas2)
        charts_row.addWidget(chart2_card)

        main_layout.addLayout(charts_row)

        # TQM Operational Standards Banner
        banner = QFrame()
        banner.setStyleSheet("background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px;")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(12, 8, 12, 8)

        tqm_label = QLabel("<b>TQM Operational Standards:</b> 14-Day Loan SLA | Rs. 5/Day Overdue Fine | 5% Tax Deductions | Bcrypt Hashing Enforced")
        tqm_label.setStyleSheet("color: #475569; font-size: 12px;")
        b_layout.addWidget(tqm_label)
        main_layout.addWidget(banner)

    def refresh_data(self):
        """Fetches latest data from analytics service and updates UI."""
        try:
            kpis = get_dashboard_kpis()
            self.card_books.update_value(str(kpis["total_books"]))
            self.card_loans.update_value(str(kpis["active_loans"]), f"{kpis['overdue_loans']} overdue")
            self.card_sla.update_value(f"{kpis['on_time_return_rate']}%", "SLA Target: >= 90%")
            self.card_defect.update_value(f"{kpis['defect_rate']}%", "Target: <= 2.0%")

            self._draw_department_chart()
            self._draw_status_chart(kpis)
            logger.info("Dashboard KPIs and charts refreshed.")
        except Exception as e:
            logger.error(f"Failed to refresh dashboard: {e}")

    def _draw_department_chart(self):
        self.fig1.clear()
        ax = self.fig1.add_subplot(111)

        df = get_department_wise_stats()
        if not df.empty and "Department" in df.columns:
            departments = df["Department"].tolist()
            counts = df["Total Loans"].tolist()
            bars = ax.barh(departments, counts, color="#3B82F6", height=0.55)
            ax.set_xlabel("Total Loans", fontsize=9, color="#64748B")
            ax.tick_params(axis="both", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#CBD5E1")
            ax.spines["bottom"].set_color("#CBD5E1")
            for bar in bars:
                w = bar.get_width()
                ax.text(w + 0.1, bar.get_y() + bar.get_height()/2, f"{int(w)}",
                        va="center", ha="left", fontsize=8, color="#1E293B")
        else:
            ax.text(0.5, 0.5, "No loan records yet", ha="center", va="center", color="#94A3B8")
            ax.axis("off")

        self.fig1.tight_layout()
        self.canvas1.draw()

    def _draw_status_chart(self, kpis: dict):
        self.fig2.clear()
        ax = self.fig2.add_subplot(111)

        active = kpis.get("active_loans", 0) - kpis.get("overdue_loans", 0)
        overdue = kpis.get("overdue_loans", 0)
        returned = kpis.get("returned_loans", 0)

        labels = []
        sizes = []
        colors = []

        if returned > 0:
            labels.append(f"Returned ({returned})")
            sizes.append(returned)
            colors.append("#10B981")
        if active > 0:
            labels.append(f"Borrowed ({active})")
            sizes.append(active)
            colors.append("#3B82F6")
        if overdue > 0:
            labels.append(f"Overdue ({overdue})")
            sizes.append(overdue)
            colors.append("#EF4444")

        if sizes:
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct="%1.0f%%",
                startangle=140, colors=colors,
                textprops={"fontsize": 8},
                wedgeprops={"edgecolor": "white", "linewidth": 2}
            )
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontweight("bold")
        else:
            ax.text(0.5, 0.5, "No loans data", ha="center", va="center", color="#94A3B8")
            ax.axis("off")

        self.fig2.tight_layout()
        self.canvas2.draw()
