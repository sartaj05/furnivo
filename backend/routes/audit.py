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
    if resource:
        query = query.where(AuditLog.resource_type == resource)
    items = db.session.scalars(query).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})
