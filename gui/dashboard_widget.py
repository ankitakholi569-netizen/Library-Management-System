"""
Dashboard Widget — Real-Time TQM Metrics & Embedded Analytics Charts.
Course: BBAT104 - Total Quality Management.
Visualizes process capability, circulation SLA on-time rate, and defect tolerances.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sqlalchemy import select, func
from database.db import get_db
from database.models import Book, Member, Loan, StaffShift, StaffPayroll, QualityLog
from config.settings import TQM_CONFIG
from services.logger_service import get_logger

logger = get_logger("gui.dashboard")


class StatCard(QFrame):
    """Modern KPI metric card with title, large numeric value, and status subtitle."""

    def __init__(self, title: str, value: str = "0", subtitle: str = "", accent_color: str = "#2563EB", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("cardFrame")
        self.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                border-left: 4px solid {accent_color};
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: #0F172A; font-size: 26px; font-weight: 800;")

        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("color: #94A3B8; font-size: 11px;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)

    def update_value(self, value: str, subtitle: str = ""):
        self.value_label.setText(str(value))
        if subtitle:
            self.sub_label.setText(str(subtitle))

    def set_value(self, value: str):
        self.value_label.setText(str(value))


class DashboardWidget(QWidget):
    """
    Executive TQM Analytics Dashboard with real-time KPI cards and visual Matplotlib charts.
    """

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
        page_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0F172A;")
        sub_title = QLabel("Real-Time Process Monitoring, Circulation SLA & Quality Compliance (BBAT104)")
        sub_title.setStyleSheet("font-size: 13px; color: #64748B;")
        title_box.addWidget(page_title)
        title_box.addWidget(sub_title)
        header_row.addLayout(title_box)

        header_row.addStretch()

        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 600;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_row.addWidget(self.refresh_btn)
        main_layout.addLayout(header_row)

        # Scrollable Content Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # KPI Cards Grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(14)

        self.card_books = StatCard("Textbook Catalog", "0", "Total curriculum volumes", "#2563EB")
        self.card_loans = StatCard("Active Loans", "0", "In-circulation borrowings", "#F59E0B")
        self.card_members = StatCard("Registered Patrons", "0", "Students & Faculty", "#8B5CF6")
        self.card_sla = StatCard("On-Time SLA Rate", "100%", "Target: >= 90.0%", "#10B981")
        self.card_defect = StatCard("Inventory Defect Rate", "0.0%", "Tolerance: <= 3.0%", "#EF4444")
        self.card_shifts = StatCard("Logged Shifts", "0", "Operational staff shifts", "#06B6D4")

        kpi_grid.addWidget(self.card_books, 0, 0)
        kpi_grid.addWidget(self.card_loans, 0, 1)
        kpi_grid.addWidget(self.card_members, 0, 2)
        kpi_grid.addWidget(self.card_sla, 1, 0)
        kpi_grid.addWidget(self.card_defect, 1, 1)
        kpi_grid.addWidget(self.card_shifts, 1, 2)

        self.content_layout.addLayout(kpi_grid)

        # Charts Row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)

        # Chart 1: Circulation Status
        chart1_frame = QFrame()
        chart1_frame.setObjectName("cardFrame")
        chart1_frame.setStyleSheet("QFrame#cardFrame { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }")
        c1_layout = QVBoxLayout(chart1_frame)
        c1_title = QLabel("Circulation SLA & Return Compliance")
        c1_title.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px; margin-bottom: 4px;")
        c1_layout.addWidget(c1_title)

        self.fig1 = Figure(figsize=(4.5, 3.2), dpi=100, facecolor="#FFFFFF")
        self.canvas1 = FigureCanvas(self.fig1)
        c1_layout.addWidget(self.canvas1)
        charts_row.addWidget(chart1_frame)

        # Chart 2: Category Breakdown
        chart2_frame = QFrame()
        chart2_frame.setObjectName("cardFrame")
        chart2_frame.setStyleSheet("QFrame#cardFrame { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }")
        c2_layout = QVBoxLayout(chart2_frame)
        c2_title = QLabel("Textbook Distribution by Department")
        c2_title.setStyleSheet("font-weight: 700; color: #0F172A; font-size: 14px; margin-bottom: 4px;")
        c2_layout.addWidget(c2_title)

        self.fig2 = Figure(figsize=(4.5, 3.2), dpi=100, facecolor="#FFFFFF")
        self.canvas2 = FigureCanvas(self.fig2)
        c2_layout.addWidget(self.canvas2)
        charts_row.addWidget(chart2_frame)

        self.content_layout.addLayout(charts_row)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def refresh_data(self):
        """Fetches live metrics from SQLite database and redraws charts."""
        with get_db() as db:
            total_books = db.scalar(select(func.count(Book.id))) or 0
            defect_books = db.scalar(select(func.count(Book.id)).where(Book.defect_flag == True)) or 0
            total_members = db.scalar(select(func.count(Member.id))) or 0
            active_loans = db.scalar(select(func.count(Loan.id)).where(Loan.status.in_(["Borrowed", "Overdue"]))) or 0
            overdue_loans = db.scalar(select(func.count(Loan.id)).where(Loan.status == "Overdue")) or 0
            returned_loans = db.scalar(select(func.count(Loan.id)).where(Loan.status == "Returned")) or 0
            total_loans = db.scalar(select(func.count(Loan.id))) or 0
            total_shifts = db.scalar(select(func.count(StaffShift.id))) or 0

            # Categories count
            cat_query = db.execute(select(Book.category, func.count(Book.id)).group_by(Book.category)).fetchall()
            cat_labels = [r[0] for r in cat_query]
            cat_counts = [r[1] for r in cat_query]

        # Calculate TQM metrics
        on_time_rate = 100.0 if total_loans == 0 else round(((total_loans - overdue_loans) / total_loans) * 100.0, 1)
        defect_rate = 0.0 if total_books == 0 else round((defect_books / total_books) * 100.0, 1)

        # Update KPI Cards
        self.card_books.update_value(str(total_books))
        self.card_loans.update_value(str(active_loans), f"{overdue_loans} Overdue")
        self.card_members.update_value(str(total_members))
        self.card_sla.update_value(f"{on_time_rate}%", "Compliant" if on_time_rate >= 90 else "SLA Warning")
        self.card_defect.update_value(f"{defect_rate}%", "Within Tolerance" if defect_rate <= 3.0 else "Needs Inspection")
        self.card_shifts.update_value(str(total_shifts))

        # Render Chart 1 (Donut Chart: Loan Status)
        self.fig1.clear()
        ax1 = self.fig1.add_subplot(111)
        borrowed_on_time = max(0, active_loans - overdue_loans)
        labels = ["Returned", "On-Time Loan", "Overdue"]
        sizes = [returned_loans, borrowed_on_time, overdue_loans]
        colors = ["#10B981", "#2563EB", "#EF4444"]

        if sum(sizes) == 0:
            sizes = [1]
            labels = ["No Loans"]
            colors = ["#CBD5E1"]

        wedges, texts, autotexts = ax1.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=140,
            wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 2},
        )
        for t in autotexts:
            t.set_fontsize(9)
            t.set_fontweight("bold")
            t.set_color("white")
        for t in texts:
            t.set_fontsize(9)
            t.set_color("#0F172A")
        ax1.axis("equal")
        self.fig1.tight_layout()
        self.canvas1.draw()

        # Render Chart 2 (Horizontal Bar Chart: Categories)
        self.fig2.clear()
        ax2 = self.fig2.add_subplot(111)
        if cat_labels and cat_counts:
            short_labels = [c[:18] for c in cat_labels]
            bars = ax2.barh(short_labels, cat_counts, color="#3B82F6", height=0.6)
            ax2.bar_label(bars, padding=4, fontsize=9, color="#0F172A", fontweight="bold")
            ax2.set_xlabel("Curriculum Titles", fontsize=9, color="#64748B")
            ax2.tick_params(axis="both", labelsize=8, colors="#0F172A")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            ax2.spines["left"].set_color("#E2E8F0")
            ax2.spines["bottom"].set_color("#E2E8F0")
        else:
            ax2.text(0.5, 0.5, "No Category Data", ha="center", va="center", color="#94A3B8")
            ax2.axis("off")

        self.fig2.tight_layout()
        self.canvas2.draw()
        logger.info("Dashboard KPIs and charts refreshed.")
