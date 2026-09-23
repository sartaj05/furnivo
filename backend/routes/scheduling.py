from datetime import date
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import DeliverySchedule, Order, QuoteClientAccess
from ..services.audit import record_audit
from ..services.notifications import notify_quote_client
from ..utils import current_user, roles_required

scheduling_bp = Blueprint('scheduling', __name__)


@scheduling_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_schedules():
    query = db.select(DeliverySchedule).order_by(DeliverySchedule.scheduled_date)
    if current_user().role == 'client':
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()
        query = query.join(DeliverySchedule.order).where(Order.quote_id.in_(quote_ids or [-1]))
    items = db.session.scalars(query).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@scheduling_bp.post('')
@roles_required('admin', 'sales')
def create_schedule():
    payload = request.get_json(silent=True) or {}
    if not payload.get('order_id') or not payload.get('scheduled_date'):
        return jsonify({'message': 'Order and scheduled date are required.'}), 400
    try:
        item = DeliverySchedule(order_id=int(payload['order_id']), schedule_type=str(payload.get('schedule_type', 'Delivery')), scheduled_date=date.fromisoformat(payload['scheduled_date']), time_slot=str(payload.get('time_slot', 'Morning')), assigned_team=str(payload.get('assigned_team', '')).strip(), eta=str(payload.get('eta', '')).strip(), status='Scheduled', proof_url=str(payload.get('proof_url', '')).strip(), notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
        db.session.add(item); db.session.commit()
        notify_quote_client(item.order.quote, 'Schedule confirmed', f'{item.schedule_type} scheduled for {item.scheduled_date.isoformat()}.', 'order')
        record_audit(current_user().id, 'Schedule created', 'schedule', item.id, item.schedule_type); db.session.commit()
    except ValueError as exc:
        db.session.rollback(); return jsonify({'message': str(exc)}), 400
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@scheduling_bp.patch('/<int:schedule_id>')
@roles_required('admin', 'sales')
def update_schedule(schedule_id):
    item = db.get_or_404(DeliverySchedule, schedule_id); payload = request.get_json(silent=True) or {}
    for field in ['time_slot', 'assigned_team', 'status', 'proof_url', 'notes', 'eta']:
        if field in payload: setattr(item, field, str(payload[field]).strip())
    if 'scheduled_date' in payload: item.scheduled_date = date.fromisoformat(payload['scheduled_date'])
    db.session.commit(); notify_quote_client(item.order.quote, 'Schedule updated', f'{item.schedule_type} is now {item.status}.', 'order'); record_audit(current_user().id, 'Schedule updated', 'schedule', item.id, item.status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@scheduling_bp.post('/<int:schedule_id>/confirm')
@roles_required('admin', 'sales', 'client')
def confirm_schedule(schedule_id):
    item = db.get_or_404(DeliverySchedule, schedule_id)
    if current_user().role == 'client':
        allowed = db.session.scalar(db.select(QuoteClientAccess.id).where(QuoteClientAccess.user_id == current_user().id, QuoteClientAccess.quote_id == item.order.quote_id))
        if not allowed: return jsonify({'message': 'You cannot confirm this schedule.'}), 403
    item.customer_confirmed = True; db.session.commit(); notify_quote_client(item.order.quote, 'Delivery confirmed', f'{item.schedule_type} on {item.scheduled_date.isoformat()} is confirmed.', 'order'); record_audit(current_user().id, 'Schedule confirmed by customer', 'schedule', item.id, item.schedule_type); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@scheduling_bp.post('/<int:schedule_id>/proof')
@roles_required('admin', 'sales')
def save_schedule_proof(schedule_id):
    item = db.get_or_404(DeliverySchedule, schedule_id); payload = request.get_json(silent=True) or {}
    item.proof_url = str(payload.get('proof_url', item.proof_url)).strip(); item.notes = str(payload.get('notes', item.notes)).strip(); item.status = 'Completed'
    db.session.commit(); notify_quote_client(item.order.quote, 'Delivery completed', f'{item.schedule_type} completion proof is available.', 'order'); record_audit(current_user().id, 'Schedule proof captured', 'schedule', item.id, item.proof_url); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
