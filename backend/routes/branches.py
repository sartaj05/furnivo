from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Branch, User, UserBranch, Warehouse
from ..services.audit import record_audit
from ..utils import current_user, roles_required

branches_bp = Blueprint('branches', __name__)


@branches_bp.get('')
@roles_required('admin', 'sales', 'designer')
def list_branches():
    items = db.session.scalars(db.select(Branch).where(Branch.is_active.is_(True)).order_by(Branch.name)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@branches_bp.post('')
@roles_required('admin')
def create_branch():
    payload = request.get_json(silent=True) or {}; name = str(payload.get('name', '')).strip(); code = str(payload.get('code', '')).strip().upper()
    if not name or not code: return jsonify({'message': 'Branch name and code are required.'}), 400
    if db.session.scalar(db.select(Branch).where((Branch.name == name) | (Branch.code == code))): return jsonify({'message': 'Branch name or code already exists.'}), 409
    item = Branch(name=name, code=code, address=str(payload.get('address', '')).strip(), manager=str(payload.get('manager', '')).strip())
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Branch created', 'branch', item.id, item.code); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@branches_bp.get('/<int:branch_id>/users')
@roles_required('admin')
def list_branch_users(branch_id):
    db.get_or_404(Branch, branch_id); items = db.session.scalars(db.select(UserBranch).where(UserBranch.branch_id == branch_id).order_by(UserBranch.id)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@branches_bp.post('/<int:branch_id>/users')
@roles_required('admin')
def assign_branch_user(branch_id):
    db.get_or_404(Branch, branch_id); payload = request.get_json(silent=True) or {}
    user = db.session.get(User, payload.get('user_id')) if payload.get('user_id') else None
    if not user: return jsonify({'message': 'Valid user is required.'}), 400
    item = db.session.scalar(db.select(UserBranch).where(UserBranch.branch_id == branch_id, UserBranch.user_id == user.id))
    if not item: item = UserBranch(branch_id=branch_id, user_id=user.id, is_primary=bool(payload.get('is_primary', False))); db.session.add(item)
    else: item.is_primary = bool(payload.get('is_primary', item.is_primary))
    db.session.commit(); record_audit(current_user().id, 'User assigned to branch', 'branch', branch_id, user.email); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201
