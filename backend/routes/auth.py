from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import User
from ..utils import current_user

auth_bp = Blueprint('auth', __name__)


def auth_payload(user, status=200):
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'name': user.name},
    )
    return jsonify({'token': token, 'user': user.public_dict(), 'mode': 'api'}), status


@auth_bp.post('/register')
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))

    if len(name) < 2 or '@' not in email or len(password) < 8:
        return jsonify({'message': 'Use a valid name, email and an 8+ character password.'}), 400

    exists = db.session.scalar(db.select(User).where(func.lower(User.email) == email))
    if exists:
        return jsonify({'message': 'An account with this email already exists.'}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role='client',
    )
    db.session.add(user)
    db.session.commit()
    return auth_payload(user, 201)


@auth_bp.post('/login')
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))

    user = db.session.scalar(db.select(User).where(func.lower(User.email) == email))
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid email or password'}), 401

    return auth_payload(user)


@auth_bp.get('/me')
@jwt_required()
def me():
    user = current_user()
    if not user or not user.is_active:
        return jsonify({'message': 'Unauthorized'}), 401
    return jsonify({'user': user.public_dict(), 'mode': 'api'})
