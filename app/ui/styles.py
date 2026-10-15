"""
Executive Slate Theme & QSS Stylesheet for CampusLib Pro.
Crafted for modern, polished desktop appearance adhering to TQM quality aesthetics.
"""

# Color Palette Constants
COLOR_BG_DARK = "#0F172A"       # Deep Slate 900
COLOR_SIDEBAR = "#1E293B"       # Slate 800
COLOR_SIDEBAR_HOVER = "#334155" # Slate 700
COLOR_SIDEBAR_ACTIVE = "#2563EB"# Royal Blue Accent

COLOR_BG_LIGHT = "#F8FAFC"      # Slate 50 Main Content BG
COLOR_CARD_BG = "#FFFFFF"       # Crisp White Card BG
COLOR_BORDER = "#E2E8F0"        # Slate 200 Border
COLOR_BORDER_FOCUS = "#3B82F6"  # Blue 500

COLOR_TEXT_PRIMARY = "#0F172A"  # Dark Slate Text
COLOR_TEXT_SECONDARY = "#64748B"# Slate 500 Subtext
COLOR_TEXT_MUTED = "#94A3B8"    # Slate 400

COLOR_PRIMARY = "#2563EB"       # Blue 600
COLOR_PRIMARY_HOVER = "#1D4ED8" # Blue 700
COLOR_SUCCESS = "#10B981"       # Emerald 500
COLOR_WARNING = "#F59E0B"       # Amber 500
COLOR_DANGER = "#EF4444"        # Red 500
COLOR_INFO = "#06B6D4"          # Cyan 500


APP_STYLESHEET = f"""
/* Global Reset and Typography */
QWidget {{
    font-family: 'Segoe UI', 'Segoe UI Variable', Roboto, -apple-system, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    background-color: transparent;
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG_LIGHT};
}}

/* Sidebar Frame */
#sidebarFrame {{
    background-color: {COLOR_SIDEBAR};
    border-right: 1px solid #334155;
}}

#sidebarLogo {{
    color: #FFFFFF;
    font-size: 17px;
    font-weight: bold;
    padding: 18px 12px 6px 12px;
}}

#sidebarSublogo {{
    color: #94A3B8;
    font-size: 11px;
    padding: 0px 12px 18px 12px;
}}

#sidebarUserBadge {{
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 10px;
    margin: 8px 10px;
}}

/* Nav Buttons */
QPushButton.nav-btn {{
    text-align: left;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: #CBD5E1;
    background-color: transparent;
    border: none;
    margin: 3px 10px;
}}

QPushButton.nav-btn:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
    color: #FFFFFF;
}}

QPushButton.nav-btn:checked {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    font-weight: bold;
}}

/* Standard Cards */
QFrame.card {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
}}

/* Form Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    min-height: 20px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
    background-color: #FAFAFA;
}}

/* Buttons */
QPushButton {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: #F1F5F9;
    border-color: #CBD5E1;
}}

QPushButton.primary-btn {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
}}

QPushButton.primary-btn:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton.success-btn {{
    background-color: {COLOR_SUCCESS};
    color: #FFFFFF;
    border: none;
}}

QPushButton.success-btn:hover {{
    background-color: #059669;
}}

QPushButton.danger-btn {{
    background-color: {COLOR_DANGER};
    color: #FFFFFF;
    border: none;
}}

QPushButton.danger-btn:hover {{
    background-color: #DC2626;
}}

/* Tables */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #F1F5F9;
    font-size: 13px;
    selection-background-color: #EFF6FF;
    selection-color: {COLOR_TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: {COLOR_TEXT_SECONDARY};
    padding: 10px 8px;
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
    border-right: 1px solid #F1F5F9;
}}

QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid #F1F5F9;
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}

/* Status Bar */
QStatusBar {{
    background-color: #FFFFFF;
    border-top: 1px solid {COLOR_BORDER};
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
    padding: 4px 10px;
}}
"""
