from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .extensions import db
from .models import Order, ProjectOwnership, QuoteClientAccess, User


def current_user():
    identity = get_jwt_identity()
    if not identity:
        return None
    return db.session.get(User, int(identity))


def client_quote_ids(user_id=None):
    user_id = user_id or (current_user().id if current_user() else None)
    if not user_id:
        return []
    return db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == user_id)).all()


def client_can_access_order(order_id, user_id=None):
    order = db.session.get(Order, order_id)
    if not order:
        return False
    return order.quote_id in client_quote_ids(user_id)


def assigned_order_ids(user_id=None):
    user = current_user()
    user_id = user_id or (user.id if user else None)
    if not user_id:
        return []
    owned = db.session.scalars(db.select(ProjectOwnership.order_id).where(ProjectOwnership.user_id == user_id)).all()
    created = db.session.scalars(db.select(Order.id).where(Order.created_by_id == user_id)).all()
    return sorted(set(owned + created))


def staff_can_access_order(order_id, user_id=None):
    user = current_user()
    if not user or user.role == 'admin':
        return True
    if user.role == 'client':
        return client_can_access_order(order_id, user_id)
    return order_id in assigned_order_ids(user_id)


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
