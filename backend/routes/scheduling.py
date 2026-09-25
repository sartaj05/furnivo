from datetime import date
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import DeliverySchedule, Order, QuoteClientAccess
from ..services.audit import record_audit
from ..services.notifications import notify_quote_client
from ..utils import assigned_order_ids, current_user, roles_required

scheduling_bp = Blueprint('scheduling', __name__)


@scheduling_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_schedules():
    query = db.select(DeliverySchedule).order_by(DeliverySchedule.scheduled_date)
    if current_user().role == 'client':
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()
        query = query.join(DeliverySchedule.order).where(Order.quote_id.in_(quote_ids or [-1]))
    elif current_user().role == 'designer':
        query = query.join(DeliverySchedule.order).where(Order.id.in_(assigned_order_ids() or [-1]))
    items = db.session.scalars(query).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@scheduling_bp.post('')
@roles_required('admin', 'sales')
def create_schedule():
    payload = request.get_json(silent=True) or {}
    if not payload.get('order_id') or not payload.get('scheduled_date'):
        return jsonify({'message': 'Order and scheduled date are required.'}), 400
    try:
        item = DeliverySchedule(order_id=int(payload['order_id']), schedule_type=str(payload.get('schedule_type', 'Delivery')), scheduled_date=date.fromisoformat(payload['scheduled_date']), time_slot=str(payload.get('time_slot', 'Morning')), assigned_team=str(payload.get('assigned_team', '')).strip(), eta=str(payload.get('eta', '')).strip(), driver_name=str(payload.get('driver_name', '')).strip(), driver_phone=str(payload.get('driver_phone', '')).strip(), route_order=int(payload.get('route_order', 0) or 0), status='Scheduled', proof_url=str(payload.get('proof_url', '')).strip(), notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
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
    for field in ['time_slot', 'assigned_team', 'status', 'proof_url', 'notes', 'eta', 'driver_name', 'driver_phone']:
        if field in payload: setattr(item, field, str(payload[field]).strip())
    if 'route_order' in payload: item.route_order = int(payload['route_order'] or 0)
    if 'scheduled_date' in payload: item.scheduled_date = date.fromisoformat(payload['scheduled_date'])
    db.session.commit(); notify_quote_client(item.order.quote, 'Schedule updated', f'{item.schedule_type} is now {item.status}.', 'order'); record_audit(current_user().id, 'Schedule updated', 'schedule', item.id, item.status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@scheduling_bp.get('/route-plan')
@roles_required('admin')
def route_plan():
    date_filter = request.args.get('date')
    query = db.select(DeliverySchedule).where(DeliverySchedule.status.not_in(['Completed', 'Cancelled'])).order_by(DeliverySchedule.scheduled_date, DeliverySchedule.route_order, DeliverySchedule.id)
    if date_filter:
        try: query = query.where(DeliverySchedule.scheduled_date == date.fromisoformat(date_filter))
        except ValueError: return jsonify({'message': 'Date must be YYYY-MM-DD.'}), 400
    items = db.session.scalars(query).all()
    return jsonify({'route': [item.to_dict() for item in items], 'stops': len(items), 'total_distance_km': round(max(len(items) - 1, 0) * 7.5, 1), 'mode': 'api'})


@scheduling_bp.post('/route-plan/optimize')
@roles_required('admin', 'sales')
def optimize_route_plan():
    payload = request.get_json(silent=True) or {}; ids = payload.get('schedule_ids') or []
    items = db.session.scalars(db.select(DeliverySchedule).where(DeliverySchedule.id.in_([int(value) for value in ids]))).all() if ids else db.session.scalars(db.select(DeliverySchedule).where(DeliverySchedule.status.not_in(['Completed', 'Cancelled'])).order_by(DeliverySchedule.scheduled_date, DeliverySchedule.id)).all()
    for index, item in enumerate(sorted(items, key=lambda value: (value.scheduled_date, value.id)), 1): item.route_order = index
    db.session.commit(); record_audit(current_user().id, 'Delivery route optimized', 'schedule', '', f'{len(items)} stops'); db.session.commit()
    return jsonify({'route': [item.to_dict() for item in sorted(items, key=lambda value: value.route_order)], 'stops': len(items), 'mode': 'api'})


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


@scheduling_bp.post('/<int:schedule_id>/signoff')
@roles_required('admin', 'sales', 'client')
def signoff_schedule(schedule_id):
    item = db.get_or_404(DeliverySchedule, schedule_id); payload = request.get_json(silent=True) or {}; signature = str(payload.get('signature', '')).strip(); accepted = bool(payload.get('accepted', True))
    if current_user().role == 'client':
        allowed = db.session.scalar(db.select(QuoteClientAccess.id).where(QuoteClientAccess.user_id == current_user().id, QuoteClientAccess.quote_id == item.order.quote_id))
        if not allowed: return jsonify({'message': 'You cannot sign off this schedule.'}), 403
    if accepted and len(signature) < 2: return jsonify({'message': 'A customer signature or name is required.'}), 400
    if accepted:
        item.customer_confirmed = True; item.status = 'Completed'
        item.notes = f'{item.notes}\nCustomer sign-off: {signature}'.strip()
    db.session.commit(); notify_quote_client(item.order.quote, 'Delivery sign-off recorded', f'{item.schedule_type} sign-off has been recorded.', 'order'); record_audit(current_user().id, 'Delivery sign-off recorded', 'schedule', item.id, signature); db.session.commit()
    return jsonify({'item': item.to_dict(), 'signoff': {'signature': signature, 'accepted': accepted, 'signed_at': item.updated_at.isoformat()}, 'mode': 'api'})
