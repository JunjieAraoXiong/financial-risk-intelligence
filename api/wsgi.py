"""WSGI entry point: ``gunicorn -c gunicorn.conf.py api.wsgi:app``."""

from api.app import create_app

app = create_app()
