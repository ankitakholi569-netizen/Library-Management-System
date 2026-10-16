"""
CampusLib Pro — Application Entry Point.
Launches the PySide6 Executive Desktop Application with TQM Services.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from app.ui.styles import APP_STYLESHEET
from app.ui.views.login_view import LoginView
from app.ui.main_window import MainWindow
from app.services.db_service import init_database, seed_sample_data
from app.core.logger import get_logger

logger = get_logger("launcher")


def main():
    logger.info("Starting CampusLib Pro (TQM Edition v2.0.0)...")

    # 1. Ensure Database & Seed Data
    try:
        init_database()
        seed_sample_data()
    except Exception as e:
        logger.error(f"Database initialization failure: {e}")
        print(f"Error preparing database: {e}")

    # 2. Start Qt Application
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    current_window = {"main": None}

    def start_flow():
        login = LoginView()

        def on_login(user):
            main_win = MainWindow(current_user=user)
            current_window["main"] = main_win

            def on_logout():
                start_flow()

            main_win.logout_requested.connect(on_logout)
            main_win.show()

        login.login_successful.connect(on_login)
        login.exec()

    start_flow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
