"""
Library Management System (TQM Edition — BBAT104).
Unified Application Entry Point.

Launches BOTH the PySide6 Executive Desktop Application AND/OR Localhost Web Application
sharing the same core backend, database, and business services.

Usage:
    python run.py         # Launch PySide6 Desktop Application (Default)
    python run.py --web   # Launch Localhost Web Portal (http://127.0.0.1:5000)
    python run.py --all   # Launch both Web Portal and Desktop Application simultaneously
"""

import sys
import os
import subprocess
from pathlib import Path

# Automatically ensure execution in project .venv if required dependencies are missing in global python
_PROJECT_ROOT = Path(__file__).resolve().parent
_VENV_PYTHON = _PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

if _VENV_PYTHON.exists() and sys.executable.lower() != str(_VENV_PYTHON).lower():
    try:
        import PySide6
        import matplotlib
        import waitress
    except ImportError:
        res = subprocess.run([str(_VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]], cwd=str(_PROJECT_ROOT))
        sys.exit(res.returncode)

import threading
from database.seed import seed_database
from services.logger_service import get_logger

logger = get_logger("launcher")


def start_web_server(port=5000):
    """Starts the Flask localhost web portal using a production WSGI server (waitress)."""
    from web.app import create_app
    app = create_app()
    try:
        from waitress import serve
        print(f"Starting Production WSGI server (waitress) on http://127.0.0.1:{port} ...")
        serve(app, host="127.0.0.1", port=port, threads=6)
    except ImportError:
        print(f"Starting development server on http://127.0.0.1:{port} ...")
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def launch_desktop_gui():
    """Launches the PySide6 executive desktop interface."""
    from PySide6.QtWidgets import QApplication
    from gui.styles import APP_STYLESHEET
    from gui.login_dialog import LoginDialog
    from gui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    while True:
        login = LoginDialog()
        result = login.exec()

        if result != LoginDialog.Accepted or not login.authenticated_user:
            break

        # Launch Main Window with authenticated user
        main_win = MainWindow(current_user=login.authenticated_user)
        logout_flag = [False]

        def on_logout():
            logout_flag[0] = True

        main_win.logout_requested.connect(on_logout)
        main_win.show()
        app.exec()

        if not logout_flag[0]:
            break


def main():
    logger.info("Starting Library Management System (TQM Edition BBAT104)...")

    # 1. Ensure Shared SQLite Database Schema & Seed Records
    try:
        seed_database()
    except Exception as e:
        logger.error(f"Database initialization failure: {e}")
        print(f"Error preparing database: {e}")

    # 2. Check Launch Mode Flags
    args = sys.argv[1:]

    if "--web" in args:
        print("Starting Localhost Web Portal at http://127.0.0.1:5000 ...")
        start_web_server()
        return

    if "--all" in args:
        print("Starting Localhost Web Portal in background at http://127.0.0.1:5000 ...")
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        print("Launching PySide6 Desktop GUI...")
        launch_desktop_gui()
        return

    # Default: Desktop GUI
    launch_desktop_gui()


if __name__ == "__main__":
    main()
