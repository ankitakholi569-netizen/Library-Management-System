"""
Executive Slate Theme & QSS Stylesheet for Library Management System.
Course: BBAT104 - Total Quality Management.
Modern, clean desktop appearance adhering to TQM aesthetics and visual ergonomics.
"""

from config.settings import THEME_COLORS

# Core Palette
COLOR_BG_DARK = THEME_COLORS.get("bg_sidebar", "#0F172A")
COLOR_SIDEBAR_HOVER = THEME_COLORS.get("bg_sidebar_hover", "#1E293B")
COLOR_SIDEBAR_ACTIVE = THEME_COLORS.get("sidebar_active", "#2563EB")
COLOR_BG_LIGHT = THEME_COLORS.get("bg_main", "#F8FAFC")
COLOR_CARD_BG = THEME_COLORS.get("bg_card", "#FFFFFF")
COLOR_BORDER = THEME_COLORS.get("border", "#E2E8F0")

COLOR_TEXT_PRIMARY = THEME_COLORS.get("text_primary", "#0F172A")
COLOR_TEXT_SECONDARY = THEME_COLORS.get("text_muted", "#64748B")
COLOR_PRIMARY = THEME_COLORS.get("primary", "#2563EB")
COLOR_PRIMARY_DARK = THEME_COLORS.get("primary_dark", "#1D4ED8")
COLOR_PRIMARY_LIGHT = THEME_COLORS.get("primary_light", "#DBEAFE")
COLOR_SUCCESS = THEME_COLORS.get("success", "#10B981")
COLOR_WARNING = THEME_COLORS.get("warning", "#F59E0B")
COLOR_DANGER = THEME_COLORS.get("danger", "#EF4444")

APP_STYLESHEET = f"""
/* Global Reset and Modern Typography */
QWidget {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    color: {COLOR_TEXT_PRIMARY};
    background-color: transparent;
}}

QMainWindow, QDialog {{
    background-color: {COLOR_BG_LIGHT};
}}

/* Sidebar Frame */
#sidebarFrame {{
    background-color: {COLOR_BG_DARK};
    border-right: 1px solid #1E293B;
}}

#sidebarLogo {{
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 800;
    padding: 16px 12px 4px 12px;
}}

#sidebarSublogo {{
    color: #94A3B8;
    font-size: 11px;
    padding: 0px 12px 16px 12px;
}}

QPushButton#navBtn {{
    text-align: left;
    padding: 11px 16px;
    border: none;
    border-radius: 8px;
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
    margin: 2px 10px;
    background-color: transparent;
}}

QPushButton#navBtn:hover {{
    background-color: {COLOR_SIDEBAR_HOVER};
    color: #FFFFFF;
}}

QPushButton#navBtn:checked, QPushButton#navBtn[active="true"] {{
    background-color: {COLOR_SIDEBAR_ACTIVE};
    color: #FFFFFF;
}}

/* Cards & Content Panels */
QFrame.card, QFrame#cardFrame {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
}}

/* Form Controls & Inputs */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 7px 12px;
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_PRIMARY};
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {COLOR_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

/* Standard Buttons */
QPushButton {{
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid {COLOR_BORDER};
    background-color: #FFFFFF;
    color: {COLOR_TEXT_PRIMARY};
}}

QPushButton:hover {{
    background-color: #F1F5F9;
}}

QPushButton.primary-btn, QPushButton#primaryBtn {{
    background-color: {COLOR_PRIMARY};
    color: #FFFFFF;
    border: none;
}}

QPushButton.primary-btn:hover, QPushButton#primaryBtn:hover {{
    background-color: {COLOR_PRIMARY_DARK};
}}

QPushButton.success-btn, QPushButton#successBtn {{
    background-color: {COLOR_SUCCESS};
    color: #FFFFFF;
    border: none;
}}

QPushButton.success-btn:hover {{
    background-color: #059669;
}}

QPushButton.danger-btn, QPushButton#dangerBtn {{
    background-color: {COLOR_DANGER};
    color: #FFFFFF;
    border: none;
}}

QPushButton.danger-btn:hover {{
    background-color: #DC2626;
}}

/* Table Widget Styling */
QTableWidget {{
    background-color: {COLOR_CARD_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    gridline-color: #F1F5F9;
    selection-background-color: {COLOR_PRIMARY_LIGHT};
    selection-color: {COLOR_TEXT_PRIMARY};
    outline: none;
}}

QHeaderView::section {{
    background-color: #F8FAFC;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 700;
    font-size: 12px;
    padding: 9px 12px;
    border: none;
    border-bottom: 2px solid {COLOR_BORDER};
}}

QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid #F1F5F9;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
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

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    background-color: {COLOR_CARD_BG};
}}

QTabBar::tab {{
    background-color: #F1F5F9;
    color: {COLOR_TEXT_SECONDARY};
    font-weight: 600;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_CARD_BG};
    color: {COLOR_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
}}
"""
