"""Vercel serverless entry point (routes all requests to the Flask app).

Requires ``vercel-wsgi`` (see requirements.txt). The app must receive a
DATABASE_URL (e.g. Vercel Postgres) because Vercel's filesystem is read-only
and the local SQLite file cannot be created there.
"""
from vercel_wsgi import handle_wsgi

from app import app as application

app = handle_wsgi(application)
