from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import InventoryItem, Product, ProductVariant
from ..utils import roles_required

inventory_bp = Blueprint('inventory', __name__)


def apply_payload(item, payload):
    for field in ['quantity', 'reserved_quantity', 'reorder_level']:
        if field in payload:
            try:
                value = Decimal(str(payload[field] or 0))
            except (InvalidOperation, ValueError):
                raise ValueError(f'{field} must be a valid number.')
            if value < 0:
                raise ValueError(f'{field} cannot be negative.')
            setattr(item, field, value)
    for field in ['supplier', 'location']:
        if field in payload:
            setattr(item, field, str(payload[field]).strip())
    return item


@inventory_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_inventory():
    items = db.session.scalars(db.select(InventoryItem).order_by(InventoryItem.id)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@inventory_bp.post('')
@roles_required('admin')
def create_inventory():
    payload = request.get_json(silent=True) or {}
    product = db.session.get(Product, int(payload.get('product_id'))) if payload.get('product_id') else None
    variant = db.session.get(ProductVariant, int(payload.get('variant_id'))) if payload.get('variant_id') else None
    if not product:
        return jsonify({'message': 'Choose a valid product.'}), 400
    if variant and variant.product_id != product.id:
        return jsonify({'message': 'Variant does not belong to this product.'}), 400
    if db.session.scalar(db.select(InventoryItem).where(InventoryItem.product_id == product.id, InventoryItem.variant_id == (variant.id if variant else None))):
        return jsonify({'message': 'Inventory already exists for this product selection.'}), 409
    item = InventoryItem(product_id=product.id, variant_id=variant.id if variant else None)
    try:
        apply_payload(item, payload)
        db.session.add(item)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@inventory_bp.patch('/<int:item_id>')
@roles_required('admin', 'sales')
def update_inventory(item_id):
    item = db.get_or_404(InventoryItem, item_id)
    try:
        apply_payload(item, request.get_json(silent=True) or {})
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
