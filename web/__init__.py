"""
Web Package for Library Management System.
Exports Flask application factory and shared web app instance.
"""

from web.app import create_app, app

__all__ = ["create_app", "app"]
