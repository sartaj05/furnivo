import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import MfaChallenge, MfaSetting, PasswordResetToken, RefreshSession, User
from ..utils import current_user, roles_required

auth_bp = Blueprint('auth', __name__)
_failed_logins = {}


def token_hash(value): return hashlib.sha256(value.encode()).hexdigest()


def auth_payload(user, status=200):
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'name': user.name},
    )
    raw_refresh = secrets.token_urlsafe(48)
    session = RefreshSession(user_id=user.id, token_hash=token_hash(raw_refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=current_app.config['REFRESH_TOKEN_DAYS']), user_agent=request.headers.get('User-Agent', ''), ip_address=request.remote_addr or '')
    db.session.add(session); db.session.commit()
    response = jsonify({'token': token, 'user': user.public_dict(), 'mode': 'api'})
    secure = current_app.config['ENVIRONMENT'] == 'production'
    response.set_cookie('access_token_cookie', token, httponly=True, secure=secure, samesite='Lax', max_age=int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()))
    response.set_cookie('refresh_token', raw_refresh, httponly=True, secure=secure, samesite='Lax', max_age=current_app.config['REFRESH_TOKEN_DAYS'] * 86400)
    return response, status


def login_key(email):
    return f'{email}:{request.remote_addr or "unknown"}'


def login_lock(key):
    item = _failed_logins.get(key)
    if not item or not item.get('until'): return None
    if item['until'] <= datetime.now(timezone.utc):
        _failed_logins.pop(key, None); return None
    return item


def record_login_failure(key):
    item = _failed_logins.get(key) or {'attempts': 0, 'until': None}
    item['attempts'] += 1
    if item['attempts'] >= current_app.config.get('LOGIN_MAX_ATTEMPTS', 5):
        item['until'] = datetime.now(timezone.utc) + timedelta(minutes=current_app.config.get('LOGIN_LOCKOUT_MINUTES', 15))
    _failed_logins[key] = item
    return item


@auth_bp.post('/register')
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))

    if len(name) < 2 or '@' not in email or len(password) < 10 or not any(char.isupper() for char in password) or not any(char.islower() for char in password) or not any(char.isdigit() for char in password):
        return jsonify({'message': 'Use a valid name, email and a 10+ character password with upper, lower and numeric characters.'}), 400

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

    key = login_key(email)
    locked = login_lock(key)
    if locked: return jsonify({'message': 'Too many failed attempts. Try again later.', 'retry_after_seconds': max(1, int((locked['until'] - datetime.now(timezone.utc)).total_seconds()))}), 429
    user = db.session.scalar(db.select(User).where(func.lower(User.email) == email))
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        record_login_failure(key)
        return jsonify({'message': 'Invalid email or password'}), 401
    _failed_logins.pop(key, None)
    if user.role == 'admin' and current_app.config.get('REQUIRE_MFA_FOR_ADMIN', False):
        setting = db.session.scalar(db.select(MfaSetting).where(MfaSetting.user_id == user.id))
        if not setting or not setting.enabled: return jsonify({'message': 'MFA is required for administrator accounts.'}), 403

    setting = db.session.scalar(db.select(MfaSetting).where(MfaSetting.user_id == user.id))
    if setting and setting.enabled:
        code = f'{secrets.randbelow(1000000):06d}'
        challenge = MfaChallenge(user_id=user.id, code_hash=token_hash(code), expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
        db.session.add(challenge); db.session.commit()
        payload = {'mfa_required': True, 'challenge_id': challenge.id, 'mode': 'api'}
        if current_app.config['ENVIRONMENT'] != 'production': payload['demo_code'] = code
        return jsonify(payload), 202
    return auth_payload(user)


def valid_password(password):
    return len(password) >= current_app.config.get('PASSWORD_MIN_LENGTH', 10) and any(char.isupper() for char in password) and any(char.islower() for char in password) and any(char.isdigit() for char in password)


@auth_bp.post('/forgot-password')
def forgot_password():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get('email', '')).strip().lower()
    user = db.session.scalar(db.select(User).where(func.lower(User.email) == email, User.is_active.is_(True))) if email else None
    response = {'message': 'If an active account matches that email, reset instructions are ready.', 'mode': 'api'}
    if user:
        raw_token = secrets.token_urlsafe(32)
        db.session.add(PasswordResetToken(user_id=user.id, token_hash=token_hash(raw_token), expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)))
        db.session.commit()
        if current_app.config['ENVIRONMENT'] != 'production': response['reset_token'] = raw_token
    return jsonify(response)


@auth_bp.post('/reset-password')
def reset_password():
    payload = request.get_json(silent=True) or {}
    raw_token = str(payload.get('token', '')).strip()
    password = str(payload.get('password', ''))
    if not raw_token or not valid_password(password):
        return jsonify({'message': 'Use a valid reset token and a 10+ character password with upper, lower and numeric characters.'}), 400
    item = db.session.scalar(db.select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash(raw_token)))
    if not item or not item.is_valid() or not item.user or not item.user.is_active:
        return jsonify({'message': 'This reset link is invalid or expired.'}), 400
    item.user.password_hash = generate_password_hash(password); item.used_at = datetime.now(timezone.utc)
    now = datetime.now(timezone.utc)
    for session in db.session.scalars(db.select(RefreshSession).where(RefreshSession.user_id == item.user_id, RefreshSession.revoked_at.is_(None))).all(): session.revoked_at = now
    db.session.commit()
    return jsonify({'message': 'Password updated. You can now sign in.', 'mode': 'api'})


@auth_bp.get('/me')
@jwt_required()
def me():
    user = current_user()
    if not user or not user.is_active:
        return jsonify({'message': 'Unauthorized'}), 401
    return jsonify({'user': user.public_dict(), 'mode': 'api'})


@auth_bp.post('/refresh')
def refresh():
    raw = request.cookies.get('refresh_token') or str((request.get_json(silent=True) or {}).get('refresh_token', ''))
    session = db.session.scalar(db.select(RefreshSession).where(RefreshSession.token_hash == token_hash(raw))) if raw else None
    now = datetime.now(timezone.utc)
    expiry = session.expires_at.replace(tzinfo=timezone.utc) if session and session.expires_at and session.expires_at.tzinfo is None else session.expires_at if session else None
    if not session or session.revoked_at or expiry <= now or not session.user.is_active:
        return jsonify({'message': 'Refresh session is invalid or expired.'}), 401
    session.revoked_at = now
    return auth_payload(session.user)


@auth_bp.post('/logout')
def logout():
    raw = request.cookies.get('refresh_token') or str((request.get_json(silent=True) or {}).get('refresh_token', ''))
    session = db.session.scalar(db.select(RefreshSession).where(RefreshSession.token_hash == token_hash(raw))) if raw else None
    if session: session.revoked_at = datetime.now(timezone.utc); db.session.commit()
    response = jsonify({'ok': True, 'mode': 'api'}); response.delete_cookie('access_token_cookie'); response.delete_cookie('refresh_token'); return response


@auth_bp.post('/sessions/revoke-all')
@roles_required('admin', 'sales', 'designer', 'client')
def revoke_all_sessions():
    now = datetime.now(timezone.utc)
    for session in db.session.scalars(db.select(RefreshSession).where(RefreshSession.user_id == current_user().id, RefreshSession.revoked_at.is_(None))).all(): session.revoked_at = now
    db.session.commit(); return jsonify({'ok': True, 'mode': 'api'})


@auth_bp.get('/security')
@roles_required('admin', 'sales', 'designer', 'client')
def security_status():
    setting = db.session.scalar(db.select(MfaSetting).where(MfaSetting.user_id == current_user().id)); sessions = db.session.scalars(db.select(RefreshSession).where(RefreshSession.user_id == current_user().id).order_by(RefreshSession.id.desc()).limit(10)).all()
    return jsonify({'mfa_enabled': bool(setting and setting.enabled), 'mfa_method': setting.method if setting else None, 'sessions': [session.to_dict() for session in sessions], 'policy': {'mfa_required_for_admin': current_app.config.get('REQUIRE_MFA_FOR_ADMIN', False), 'max_login_attempts': current_app.config.get('LOGIN_MAX_ATTEMPTS', 5), 'lockout_minutes': current_app.config.get('LOGIN_LOCKOUT_MINUTES', 15), 'minimum_password_length': current_app.config.get('PASSWORD_MIN_LENGTH', 10)}, 'mode': 'api'})


@auth_bp.post('/mfa/enable')
@roles_required('admin', 'sales', 'designer', 'client')
def enable_mfa():
    setting = db.session.scalar(db.select(MfaSetting).where(MfaSetting.user_id == current_user().id))
    if not setting: setting = MfaSetting(user_id=current_user().id); db.session.add(setting)
    setting.enabled = True; db.session.commit(); return jsonify({'enabled': True, 'method': setting.method, 'message': 'MFA enabled. Future logins require a one-time code.', 'mode': 'api'})


@auth_bp.post('/mfa/disable')
@roles_required('admin', 'sales', 'designer', 'client')
def disable_mfa():
    setting = db.session.scalar(db.select(MfaSetting).where(MfaSetting.user_id == current_user().id))
    if setting: setting.enabled = False; db.session.commit()
    return jsonify({'enabled': False, 'mode': 'api'})


@auth_bp.post('/mfa/verify')
def verify_mfa():
    payload = request.get_json(silent=True) or {}; challenge = db.session.get(MfaChallenge, int(payload.get('challenge_id'))) if payload.get('challenge_id') else None
    expiry = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge and challenge.expires_at and challenge.expires_at.tzinfo is None else challenge.expires_at if challenge else None
    if not challenge or challenge.consumed_at or expiry <= datetime.now(timezone.utc) or challenge.code_hash != token_hash(str(payload.get('code', '')).strip()): return jsonify({'message': 'Invalid or expired MFA code.'}), 401
    challenge.consumed_at = datetime.now(timezone.utc); db.session.commit(); return auth_payload(challenge.user)
