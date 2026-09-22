import json
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Customer, CustomerPricing, QuotePreset
from ..services.audit import record_audit
from ..utils import current_user, roles_required

configurator_bp = Blueprint('configurator', __name__)
CONFIGURATOR_ROLES = ('admin', 'sales', 'designer')


@configurator_bp.get('/presets')
@roles_required(*CONFIGURATOR_ROLES)
def list_presets():
    items = db.session.scalars(db.select(QuotePreset).order_by(QuotePreset.name)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@configurator_bp.post('/presets')
@roles_required(*CONFIGURATOR_ROLES)
def create_preset():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    items = payload.get('items') if isinstance(payload.get('items'), list) else []
    if not name or not items:
        return jsonify({'message': 'Preset name and at least one product are required.'}), 400
    try:
        discount = Decimal(str(payload.get('discount_percent', 0)))
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Preset discount must be valid.'}), 400
    if discount < 0 or discount > 100:
        return jsonify({'message': 'Preset discount must be between 0 and 100.'}), 400
    item = QuotePreset(
        name=name,
        kind=str(payload.get('kind', 'Template')).strip() or 'Template',
        room=str(payload.get('room', '')).strip(),
        description=str(payload.get('description', '')).strip(),
        discount_percent=discount,
        items_json=json.dumps(items),
        created_by_id=current_user().id,
    )
    db.session.add(item)
    db.session.commit()
    record_audit(current_user().id, 'Quotation preset created', 'quote_preset', item.id, item.name)
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@configurator_bp.get('/pricing/<int:customer_id>')
@roles_required(*CONFIGURATOR_ROLES)
def get_customer_pricing(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    item = db.session.scalar(db.select(CustomerPricing).where(CustomerPricing.customer_id == customer.id))
    if not item:
        return jsonify({'item': {'customer_id': customer.id, 'customer': customer.company, 'tier': 'Standard', 'discount_percent': 0}, 'mode': 'api'})
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@configurator_bp.put('/pricing/<int:customer_id>')
@roles_required('admin', 'sales')
def save_customer_pricing(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    payload = request.get_json(silent=True) or {}
    try:
        discount = Decimal(str(payload.get('discount_percent', 0)))
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Customer discount must be valid.'}), 400
    if discount < 0 or discount > 100:
        return jsonify({'message': 'Customer discount must be between 0 and 100.'}), 400
    item = db.session.scalar(db.select(CustomerPricing).where(CustomerPricing.customer_id == customer.id))
    if not item:
        item = CustomerPricing(customer_id=customer.id)
        db.session.add(item)
    item.tier = str(payload.get('tier', 'Standard')).strip() or 'Standard'
    item.discount_percent = discount
    db.session.commit()
    record_audit(current_user().id, 'Customer pricing updated', 'customer', customer.id, f'{item.tier} tier / {discount}%')
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
