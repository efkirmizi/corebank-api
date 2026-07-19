"""WSGI entry point for gunicorn: `gunicorn wsgi:app`."""

from app import create_app

app = create_app()
