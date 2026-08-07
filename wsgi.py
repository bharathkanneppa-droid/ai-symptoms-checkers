"""WSGI entry point for production servers (gunicorn/uwsgi).

    gunicorn --workers 2 --bind 0.0.0.0:8000 wsgi:app
"""
from app import app

if __name__ == "__main__":
    app.run()
