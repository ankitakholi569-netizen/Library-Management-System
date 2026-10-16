"""
Login View — Secure Bcrypt Authentication Dialog.
Demonstrates TQM Principle: Error Prevention & Access Control.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from app.models.base import get_db
from app.models.user import User
from app.core.security import verify_password
from app.core.logger import get_logger

logger = get_logger("ui.login")


class LoginView(QDialog):
    """Authentication dialog with bcrypt password verification."""

    login_successful = Signal(object)  # Emits authenticated User dict/object

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CampusLib Pro — Secure Staff Login")
        self.setFixedSize(450, 560)
        self.authenticated_user = None

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(16)

        # Card Frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        # Header Title
        title_lbl = QLabel("CampusLib Pro")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #0F172A;")
        title_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_lbl)

        sub_lbl = QLabel("TQM Library & Staff Management")
        sub_lbl.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 500;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(sub_lbl)

        card_layout.addSpacing(10)

        # Username Input
        card_layout.addWidget(QLabel("Staff Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. admin or priya_desk")
        self.username_input.setText("admin")
        card_layout.addWidget(self.username_input)

        # Password Input
        card_layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setText("admin123")
        self.password_input.returnPressed.connect(self._handle_login)
        card_layout.addWidget(self.password_input)

        # Login Button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setProperty("class", "primary-btn")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_btn)

        # Quick Demo Login Buttons
        card_layout.addSpacing(8)
        demo_lbl = QLabel("Quick Login Presets (TQM Demo):")
        demo_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600;")
        card_layout.addWidget(demo_lbl)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(6)

        btn_admin = QPushButton("Chief Librarian")
        btn_admin.setStyleSheet("font-size: 11px; padding: 5px;")
        btn_admin.clicked.connect(lambda: self._fill_credentials("admin", "admin123"))

        btn_priya = QPushButton("Circulation Desk")
        btn_priya.setStyleSheet("font-size: 11px; padding: 5px;")
        btn_priya.clicked.connect(lambda: self._fill_credentials("priya_desk", "priya123"))

        btn_rahul = QPushButton("Catalog Staff")
        btn_rahul.setStyleSheet("font-size: 11px; padding: 5px;")
        btn_rahul.clicked.connect(lambda: self._fill_credentials("rahul_catalog", "rahul123"))

        btn_box.addWidget(btn_admin)
        btn_box.addWidget(btn_priya)
        btn_box.addWidget(btn_rahul)
        card_layout.addLayout(btn_box)

        main_layout.addWidget(card)

    def _fill_credentials(self, user: str, pwd: str):
        self.username_input.setText(user)
        self.password_input.setText(pwd)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Validation Error", "Please provide both username and password.")
            return

        with get_db() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user or not user.is_active:
                QMessageBox.critical(self, "Authentication Failed", "Invalid credentials or inactive account.")
                return

            if not verify_password(password, user.password_hash):
                QMessageBox.critical(self, "Authentication Failed", "Incorrect password provided.")
                return

            # Success
            self.authenticated_user = {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "email": user.email,
            }
            logger.info(f"User '{user.username}' logged in successfully ({user.role}).")
            self.login_successful.emit(self.authenticated_user)
            self.accept()
