from datetime import date
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Order, ProjectUpdate, Quote, QuoteClientAccess
from ..utils import current_user, roles_required

orders_bp = Blueprint('orders', __name__)


def next_order_number():
    numbers = []
    for value in db.session.scalars(db.select(Order.order_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f'ORD-{max(numbers, default=1000) + 1}'


@orders_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_orders():
    query = db.select(Order).order_by(Order.id.desc())
    if current_user().role == 'client':
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()
        query = query.where(Order.quote_id.in_(quote_ids or [-1]))
    items = db.session.scalars(query).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@orders_bp.post('')
@roles_required('admin', 'sales')
def create_order():
    payload = request.get_json(silent=True) or {}
    quote = db.session.get(Quote, int(payload.get('quote_id'))) if payload.get('quote_id') else None
    if not quote:
        return jsonify({'message': 'Choose a valid quotation.'}), 400
    if db.session.scalar(db.select(Order).where(Order.quote_id == quote.id)):
        return jsonify({'message': 'An order already exists for this quotation.'}), 409
    order = Order(
        order_number=next_order_number(),
        quote_id=quote.id,
        customer_id=quote.customer_id,
        customer_name=quote.customer_name,
        status='Confirmed',
        production_status='Not started',
        delivery_date=date.fromisoformat(payload['delivery_date']) if payload.get('delivery_date') else None,
        installation_status='Not scheduled',
        notes=str(payload.get('notes', '')).strip(),
        created_by_id=current_user().id,
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'item': order.to_dict(), 'mode': 'api'}), 201


@orders_bp.patch('/<int:order_id>')
@roles_required('admin', 'sales')
def update_order(order_id):
    order = db.get_or_404(Order, order_id)
    payload = request.get_json(silent=True) or {}
    for field in ['status', 'production_status', 'installation_status', 'notes']:
        if field in payload:
            setattr(order, field, str(payload[field]).strip())
    if 'delivery_date' in payload:
        order.delivery_date = date.fromisoformat(payload['delivery_date']) if payload['delivery_date'] else None
    db.session.commit()
    return jsonify({'item': order.to_dict(), 'mode': 'api'})


@orders_bp.post('/<int:order_id>/updates')
@roles_required('admin', 'sales', 'designer')
def add_update(order_id):
    order = db.get_or_404(Order, order_id)
    body = str((request.get_json(silent=True) or {}).get('body', '')).strip()
    if not body:
        return jsonify({'message': 'Project update cannot be empty.'}), 400
    update = ProjectUpdate(order_id=order.id, body=body, author_id=current_user().id)
    db.session.add(update)
    db.session.commit()
    return jsonify({'item': update.to_dict(), 'order': order.to_dict(), 'mode': 'api'}), 201
