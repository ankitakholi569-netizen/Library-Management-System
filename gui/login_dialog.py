"""
Login Dialog for PySide6 Desktop Application.
Course: BBAT104 - Total Quality Management.
Implements secure bcrypt credential verification with quick-preset test buttons.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt
from services.auth_service import authenticate_user
from config.settings import APP_NAME, COURSE_NAME


class LoginDialog(QDialog):
    """Secure multi-role authentication dialog with bcrypt verification."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Authentication")
        self.setFixedSize(440, 520)
        self.authenticated_user = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("cardFrame")
        card.setStyleSheet("""
            QFrame#cardFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        # Header
        t_lbl = QLabel(APP_NAME)
        t_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F172A;")
        t_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(t_lbl)

        sub_lbl = QLabel(f"TQM Edition • {COURSE_NAME}")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(sub_lbl)

        c_layout.addSpacing(8)

        # Inputs
        u_lbl = QLabel("Username")
        u_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;")
        self.username_input = QLineEdit("admin")
        self.username_input.setPlaceholderText("Enter username")

        p_lbl = QLabel("Password")
        p_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase;")
        self.password_input = QLineEdit("admin123")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")

        c_layout.addWidget(u_lbl)
        c_layout.addWidget(self.username_input)
        c_layout.addWidget(p_lbl)
        c_layout.addWidget(self.password_input)

        # Sign In Button
        self.signin_btn = QPushButton("Sign In to Portal")
        self.signin_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 14px;
                padding: 10px;
                border-radius: 6px;
                border: none;
                margin-top: 6px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.signin_btn.clicked.connect(self._handle_login)
        c_layout.addWidget(self.signin_btn)

        # Presets Box for Demo
        c_layout.addSpacing(6)
        presets_lbl = QLabel("QUICK TEST PRESETS (BBAT104 VIVA):")
        presets_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #94A3B8;")
        c_layout.addWidget(presets_lbl)

        preset_row = QHBoxLayout()
        btn_admin = QPushButton("Chief Librarian")
        btn_admin.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        btn_admin.clicked.connect(lambda: self._set_credentials("admin", "admin123"))

        btn_desk = QPushButton("Circulation Desk")
        btn_desk.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        btn_desk.clicked.connect(lambda: self._set_credentials("priya_desk", "priya123"))

        btn_catalog = QPushButton("Catalog Staff")
        btn_catalog.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        btn_catalog.clicked.connect(lambda: self._set_credentials("rahul_catalog", "rahul123"))

        preset_row.addWidget(btn_admin)
        preset_row.addWidget(btn_desk)
        preset_row.addWidget(btn_catalog)
        c_layout.addLayout(preset_row)

        main_layout.addWidget(card)

    def _set_credentials(self, username, password):
        self.username_input.setText(username)
        self.password_input.setText(password)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        ok, user_data, msg = authenticate_user(username, password)
        if not ok:
            QMessageBox.warning(self, "Authentication Failed", msg)
            return

        self.authenticated_user = user_data
        self.accept()
