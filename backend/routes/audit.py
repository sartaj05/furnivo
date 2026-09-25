from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import AuditLog
from ..utils import roles_required

audit_bp = Blueprint('audit', __name__)


@audit_bp.get('')
@roles_required('admin')
def list_audit_logs():
    query = db.select(AuditLog).order_by(AuditLog.id.desc()).limit(200)
    resource = request.args.get('resource', '').strip()
    action = request.args.get('action', '').strip()
    if resource:
        query = query.where(AuditLog.resource_type == resource)
    if action:
        query = query.where(AuditLog.action == action)
    items = db.session.scalars(query).all()
    resource_counts = {}
    action_counts = {}
    for item in items:
        resource_counts[item.resource_type] = resource_counts.get(item.resource_type, 0) + 1
        action_counts[item.action] = action_counts.get(item.action, 0) + 1
    return jsonify({'items': [item.to_dict() for item in items], 'summary': {'total': len(items), 'resources': resource_counts, 'actions': action_counts, 'last_activity': items[0].created_at.isoformat() if items else None}, 'mode': 'api'})
