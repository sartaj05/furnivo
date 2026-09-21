from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .extensions import db
from .models import User


def current_user():
    identity = get_jwt_identity()
    if not identity:
        return None
    return db.session.get(User, int(identity))


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user()
            if not user or not user.is_active:
                return jsonify({'message': 'Unauthorized'}), 401
            if roles and user.role not in roles:
                return jsonify({'message': 'Forbidden'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
