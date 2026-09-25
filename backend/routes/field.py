import json
from datetime import date, timezone
from uuid import uuid4
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import FieldVisit, Order, User
from ..models import utcnow
from ..services.audit import record_audit
from ..utils import assigned_order_ids, can_access_order, client_quote_ids, current_user, roles_required

field_bp = Blueprint('field', __name__)


def visit_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


@field_bp.get('')
@roles_required('admin', 'designer', 'client')
def list_field_visits():
    query = db.select(FieldVisit).order_by(FieldVisit.scheduled_date, FieldVisit.id.desc())
    if current_user().role == 'client':
        from ..models import Order
        query = query.join(FieldVisit.order).where(Order.quote_id.in_(client_quote_ids() or [-1]))
    elif current_user().role == 'designer':
        query = query.where(FieldVisit.order_id.in_(assigned_order_ids() or [-1]))
    items = db.session.scalars(query).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@field_bp.post('')
@roles_required('admin', 'designer')
def create_field_visit():
    payload = request.get_json(silent=True) or {}; order = db.session.get(Order, payload.get('order_id')) if payload.get('order_id') else None; scheduled = visit_date(payload.get('scheduled_date'))
    if not order or not scheduled:
        return jsonify({'message': 'Project and valid scheduled date are required.'}), 400
    item = FieldVisit(order_id=order.id, schedule_id=payload.get('schedule_id'), visit_type=str(payload.get('visit_type', 'Installation')), status='Scheduled', assigned_to_id=payload.get('assigned_to_id'), scheduled_date=scheduled, qr_token=str(payload.get('qr_token') or f'FURNIVO-{uuid4().hex[:10].upper()}'), notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Field visit scheduled', 'field_visit', item.id, item.visit_type); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@field_bp.patch('/<int:visit_id>')
@roles_required('admin', 'designer')
def update_field_visit(visit_id):
    item = db.get_or_404(FieldVisit, visit_id); payload = request.get_json(silent=True) or {}
    if not can_access_order(item.order_id): return jsonify({'message': 'You do not have access to this field visit.'}), 403
    if 'status' in payload and payload['status'] not in {'Scheduled', 'En route', 'On site', 'Completed', 'Cancelled'}:
        return jsonify({'message': 'Invalid field visit status.'}), 400
    for key in ('status', 'assigned_to_id', 'notes', 'time_minutes'):
        if key in payload: setattr(item, key, payload[key])
    db.session.commit(); record_audit(current_user().id, 'Field visit updated', 'field_visit', item.id, item.status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@field_bp.post('/<int:visit_id>/check-in')
@roles_required('admin', 'designer')
def check_in_field_visit(visit_id):
    item = db.get_or_404(FieldVisit, visit_id); payload = request.get_json(silent=True) or {}
    if not can_access_order(item.order_id): return jsonify({'message': 'You do not have access to this field visit.'}), 403
    item.check_in_at = utcnow(); item.status = 'On site'
    if payload.get('gps_lat') is not None: item.gps_lat = payload['gps_lat']
    if payload.get('gps_lng') is not None: item.gps_lng = payload['gps_lng']
    db.session.commit(); record_audit(current_user().id, 'Field visit check-in', 'field_visit', item.id, item.qr_token); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@field_bp.post('/<int:visit_id>/check-out')
@roles_required('admin', 'designer')
def check_out_field_visit(visit_id):
    item = db.get_or_404(FieldVisit, visit_id); payload = request.get_json(silent=True) or {}
    if not can_access_order(item.order_id): return jsonify({'message': 'You do not have access to this field visit.'}), 403
    item.check_out_at = utcnow(); item.status = 'Completed'
    if item.check_in_at:
        started = item.check_in_at if item.check_in_at.tzinfo else item.check_in_at.replace(tzinfo=timezone.utc)
        item.time_minutes = max(int((item.check_out_at - started).total_seconds() // 60), 0)
    if payload.get('notes') is not None: item.notes = str(payload['notes']).strip()
    db.session.commit(); record_audit(current_user().id, 'Field visit check-out', 'field_visit', item.id, f'{item.time_minutes} minutes'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@field_bp.post('/<int:visit_id>/materials')
@roles_required('admin', 'designer')
def record_field_material(visit_id):
    item = db.get_or_404(FieldVisit, visit_id); payload = request.get_json(silent=True) or {}
    if not can_access_order(item.order_id): return jsonify({'message': 'You do not have access to this field visit.'}), 403
    name = str(payload.get('name', '')).strip(); movement = str(payload.get('movement', 'issue')).lower()
    try: quantity = float(payload.get('quantity', 0))
    except (TypeError, ValueError): quantity = 0
    if not name or quantity <= 0 or movement not in {'issue', 'return'}:
        return jsonify({'message': 'Material name, positive quantity, and issue/return movement are required.'}), 400
    try: materials = json.loads(item.materials_json or '[]')
    except (TypeError, ValueError): materials = []
    materials.insert(0, {'id': uuid4().hex[:10], 'name': name, 'product_id': payload.get('product_id'), 'quantity': quantity, 'movement': movement, 'notes': str(payload.get('notes', '')).strip(), 'created_at': utcnow().isoformat()})
    item.materials_json = json.dumps(materials); db.session.commit(); record_audit(current_user().id, f'Material {movement}', 'field_visit', item.id, f'{name} x {quantity}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@field_bp.post('/<int:visit_id>/proof')
@roles_required('admin', 'designer')
def save_field_proof(visit_id):
    item = db.get_or_404(FieldVisit, visit_id); payload = request.get_json(silent=True) or {}
    if not can_access_order(item.order_id): return jsonify({'message': 'You do not have access to this field visit.'}), 403
    item.proof_photo_url = str(payload.get('proof_photo_url', item.proof_photo_url)).strip(); item.customer_signature = str(payload.get('customer_signature', item.customer_signature)).strip(); item.notes = str(payload.get('notes', item.notes)).strip(); item.offline_synced = True
    if payload.get('gps_lat') is not None: item.gps_lat = payload['gps_lat']
    if payload.get('gps_lng') is not None: item.gps_lng = payload['gps_lng']
    if item.proof_photo_url or item.customer_signature: item.status = 'Completed'
    db.session.commit(); record_audit(current_user().id, 'Field proof captured', 'field_visit', item.id, item.qr_token); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
