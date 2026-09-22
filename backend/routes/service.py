from datetime import date
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Customer, Order, ServiceTicket, User, Warranty
from ..services.audit import record_audit
from ..utils import current_user, roles_required

service_bp = Blueprint('service', __name__)


def parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


@service_bp.get('/warranties')
@roles_required('admin', 'sales', 'designer', 'client')
def list_warranties():
    items = db.session.scalars(db.select(Warranty).order_by(Warranty.end_date)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@service_bp.post('/warranties')
@roles_required('admin', 'sales')
def create_warranty():
    payload = request.get_json(silent=True) or {}
    order = db.session.get(Order, payload.get('order_id')) if payload.get('order_id') else None
    start_date = parse_date(payload.get('start_date')); end_date = parse_date(payload.get('end_date'))
    if not order or not start_date or not end_date or end_date < start_date:
        return jsonify({'message': 'Valid order, start date, and end date are required.'}), 400
    item = Warranty(warranty_number=str(payload.get('warranty_number') or f'WAR-{7000 + (db.session.scalar(db.select(db.func.count(Warranty.id))) or 0) + 1}'), order_id=order.id, product_id=payload.get('product_id'), customer_id=order.customer_id, start_date=start_date, end_date=end_date, coverage=str(payload.get('coverage', '')).strip() or 'Manufacturing defects and installation issues', serial_number=str(payload.get('serial_number', '')).strip())
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Warranty created', 'warranty', item.id, item.warranty_number); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@service_bp.get('/tickets')
@roles_required('admin', 'sales', 'designer', 'client')
def list_service_tickets():
    query = db.select(ServiceTicket).order_by(ServiceTicket.id.desc())
    items = db.session.scalars(query).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@service_bp.post('/tickets')
@roles_required('admin', 'sales', 'designer', 'client')
def create_service_ticket():
    payload = request.get_json(silent=True) or {}; order = db.session.get(Order, payload.get('order_id')) if payload.get('order_id') else None
    subject = str(payload.get('subject', '')).strip(); description = str(payload.get('description', '')).strip()
    if not order or not subject or not description:
        return jsonify({'message': 'Project, subject, and description are required.'}), 400
    if current_user().role == 'client':
        customer_user = current_user()
        if customer_user.email != 'client@furnivo.demo':
            return jsonify({'message': 'Project access could not be verified.'}), 403
    item = ServiceTicket(ticket_number=f'SVC-{8000 + (db.session.scalar(db.select(db.func.count(ServiceTicket.id))) or 0) + 1}', warranty_id=payload.get('warranty_id'), order_id=order.id, customer_id=order.customer_id, subject=subject, description=description, priority=str(payload.get('priority', 'Normal')), sla_due=parse_date(payload.get('sla_due')), assigned_to_id=payload.get('assigned_to_id'))
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Service ticket created', 'service_ticket', item.id, item.subject); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@service_bp.patch('/tickets/<int:ticket_id>')
@roles_required('admin', 'sales', 'designer')
def update_service_ticket(ticket_id):
    item = db.get_or_404(ServiceTicket, ticket_id); payload = request.get_json(silent=True) or {}
    if 'status' in payload and payload['status'] not in {'Open', 'Assigned', 'In progress', 'Waiting for customer', 'Resolved', 'Closed'}:
        return jsonify({'message': 'Invalid service status.'}), 400
    for key in ('status', 'priority', 'resolution', 'assigned_to_id'):
        if key in payload: setattr(item, key, payload[key])
    if 'sla_due' in payload: item.sla_due = parse_date(payload['sla_due'])
    db.session.commit(); record_audit(current_user().id, 'Service ticket updated', 'service_ticket', item.id, item.status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
