from functools import wraps
from flask import abort
from flask_login import current_user

def require_role(role_name: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.role or current_user.role.name != role_name:
                return abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission_code: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.role or not current_user.role.has_perm(permission_code):
                return abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
