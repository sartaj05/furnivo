import json
from datetime import datetime, timezone
from flask import Blueprint, Response, jsonify, request
from ..extensions import db
from ..models import AuditLog
from ..utils import current_user, roles_required

live_bp = Blueprint('live', __name__)


@live_bp.get('/updates')
@roles_required('admin', 'sales', 'designer', 'client')
def updates():
    query = db.select(AuditLog).order_by(AuditLog.created_at.desc()).limit(60)
    since = request.args.get('since')
    items = db.session.scalars(query).all()
    if current_user().role == 'client':
        items = [item for item in items if item.resource_type in {'quote', 'order', 'production_job', 'delivery_schedule', 'service_ticket'}]
    if since:
        items = [item for item in items if item.created_at.isoformat() > since]
    return jsonify({'items': [item.to_dict() for item in items], 'server_time': datetime.now(timezone.utc).isoformat(), 'mode': 'api'})


@live_bp.get('/stream')
@roles_required('admin', 'sales', 'designer', 'client')
def stream():
    """One-shot SSE snapshot; clients can reconnect for low-cost live refreshes."""
    items = db.session.scalars(db.select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)).all()
    if current_user().role == 'client': items = [item for item in items if item.resource_type in {'quote', 'order', 'production_job', 'delivery_schedule', 'service_ticket'}]
    payload = {'items': [item.to_dict() for item in items], 'server_time': datetime.now(timezone.utc).isoformat()}
    return Response(f'data: {json.dumps(payload)}\n\n', mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
