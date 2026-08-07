"""Role-based access-control decorators.

Guard routes so each role only reaches its own section of the app. The route
must be protected with @login_required as well - or use the composed helpers.
"""
from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required


def roles_required(*roles):
    """Require one of the given roles; otherwise 403 or redirect to login."""

    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def patient_required(func):
    """Route may only be used by logged-in patients."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_patient:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def doctor_required(func):
    """Route may only be used by logged-in doctors."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_doctor:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """Route may only be used by logged-in admins."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return wrapper
