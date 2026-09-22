from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import AccessPermission, ApprovalRequest, Department, Order, ProjectOwnership, User, UserDepartment
from ..services.audit import record_audit
from ..utils import current_user, roles_required

access_bp = Blueprint('access', __name__)
APPROVAL_TYPES = {'Discount', 'Margin', 'Refund', 'Price override', 'Sensitive action'}


@access_bp.get('/users')
@roles_required('admin')
def list_access_users():
    users = db.session.scalars(db.select(User).where(User.is_active.is_(True)).order_by(User.name)).all()
    return jsonify({'items': [{'user': user.public_dict(), 'permissions': [item.to_dict() for item in db.session.scalars(db.select(AccessPermission).where(AccessPermission.user_id == user.id).order_by(AccessPermission.permission)).all()], 'departments': [item.to_dict() for item in db.session.scalars(db.select(UserDepartment).where(UserDepartment.user_id == user.id)).all()]} for user in users], 'mode': 'api'})


@access_bp.put('/users/<int:user_id>/permissions')
@roles_required('admin')
def replace_permissions(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found.'}), 404
    payload = request.get_json(silent=True) or {}
    AccessPermission.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    for item in payload.get('permissions', []):
        permission = str(item.get('permission', '')).strip()
        if permission:
            db.session.add(AccessPermission(user_id=user_id, permission=permission, scope=str(item.get('scope', 'own')).strip() or 'own', is_enabled=bool(item.get('is_enabled', True))))
    db.session.commit()
    record_audit(current_user().id, 'Permissions updated', 'user', user.id, f'Permissions replaced for {user.email}')
    db.session.commit()
    return jsonify({'item': {'user': user.public_dict(), 'permissions': [item.to_dict() for item in AccessPermission.query.filter_by(user_id=user.id).all()]}, 'mode': 'api'})


@access_bp.get('/departments')
@roles_required('admin', 'sales', 'designer')
def list_departments():
    return jsonify({'items': [item.to_dict() for item in db.session.scalars(db.select(Department).where(Department.is_active.is_(True)).order_by(Department.name)).all()], 'mode': 'api'})


@access_bp.post('/departments')
@roles_required('admin')
def create_department():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    if not name:
        return jsonify({'message': 'Department name is required.'}), 400
    if db.session.scalar(db.select(Department).where(Department.name == name)):
        return jsonify({'message': 'Department already exists.'}), 409
    item = Department(name=name, description=str(payload.get('description', '')).strip())
    db.session.add(item); db.session.commit()
    record_audit(current_user().id, 'Department created', 'department', item.id, item.name); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@access_bp.get('/approvals')
@roles_required('admin', 'sales', 'designer')
def list_approvals():
    query = db.select(ApprovalRequest).order_by(ApprovalRequest.id.desc())
    items = db.session.scalars(query.limit(200)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@access_bp.post('/approvals')
@roles_required('admin', 'sales', 'designer')
def create_approval():
    payload = request.get_json(silent=True) or {}
    request_type = str(payload.get('request_type', '')).strip()
    if request_type not in APPROVAL_TYPES:
        return jsonify({'message': f'Request type must be one of: {", ".join(sorted(APPROVAL_TYPES))}.'}), 400
    try:
        amount = Decimal(str(payload.get('amount', 0) or 0))
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Amount must be a valid number.'}), 400
    item = ApprovalRequest(request_type=request_type, resource_type=str(payload.get('resource_type', 'quote')).strip() or 'quote', resource_id=str(payload.get('resource_id', '')).strip(), amount=amount, detail=str(payload.get('detail', '')).strip(), requested_by_id=current_user().id)
    if not item.resource_id:
        return jsonify({'message': 'Resource ID is required.'}), 400
    db.session.add(item); db.session.commit()
    record_audit(current_user().id, 'Approval requested', 'approval', item.id, f'{request_type} for {item.resource_type} {item.resource_id}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@access_bp.patch('/approvals/<int:approval_id>')
@roles_required('admin', 'sales')
def update_approval(approval_id):
    item = db.session.get(ApprovalRequest, approval_id)
    if not item:
        return jsonify({'message': 'Approval request not found.'}), 404
    status = str((request.get_json(silent=True) or {}).get('status', '')).strip()
    if status not in {'Approved', 'Rejected'}:
        return jsonify({'message': 'Status must be Approved or Rejected.'}), 400
    item.status = status; item.approved_by_id = current_user().id
    db.session.commit()
    record_audit(current_user().id, f'Approval {status.lower()}', 'approval', item.id, f'{item.request_type} for {item.resource_id}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@access_bp.get('/ownership')
@roles_required('admin', 'sales', 'designer')
def list_ownership():
    return jsonify({'items': [item.to_dict() for item in db.session.scalars(db.select(ProjectOwnership).order_by(ProjectOwnership.id.desc())).all()], 'mode': 'api'})


@access_bp.post('/ownership')
@roles_required('admin', 'sales')
def assign_ownership():
    payload = request.get_json(silent=True) or {}
    try:
        order_id, user_id = int(payload.get('order_id')), int(payload.get('user_id'))
    except (TypeError, ValueError):
        return jsonify({'message': 'Order and user are required.'}), 400
    if not db.session.get(Order, order_id) or not db.session.get(User, user_id):
        return jsonify({'message': 'Order or user not found.'}), 404
    item = db.session.scalar(db.select(ProjectOwnership).where(ProjectOwnership.order_id == order_id, ProjectOwnership.user_id == user_id))
    if not item:
        item = ProjectOwnership(order_id=order_id, user_id=user_id, assigned_by_id=current_user().id); db.session.add(item)
    item.assigned_by_id = current_user().id; db.session.commit()
    record_audit(current_user().id, 'Project owner assigned', 'order', order_id, f'Assigned to user {user_id}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201
