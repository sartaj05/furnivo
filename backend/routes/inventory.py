from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import BomItem, InventoryItem, Product, ProductVariant, ProductionJob
from ..utils import roles_required
from ..services.audit import record_audit
from ..utils import current_user

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
        record_audit(current_user().id, 'Inventory item created', 'inventory', item.id, item.product.sku); db.session.commit()
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
        record_audit(current_user().id, 'Inventory updated', 'inventory', item.id, item.product.sku); db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@inventory_bp.get('/forecast')
@roles_required('admin', 'sales', 'designer')
def inventory_forecast():
    inventory = db.session.scalars(db.select(InventoryItem)).all(); jobs = db.session.scalars(db.select(ProductionJob).where(ProductionJob.status.not_in(['Complete', 'On hold']))).all(); demand = {}
    for job in jobs:
        for bom in job.bom_items:
            if bom.product_id: demand[bom.product_id] = demand.get(bom.product_id, 0) + float(bom.quantity or 0) * (1 + float(bom.wastage_percent or 0) / 100)
    items = []
    for item in inventory:
        projected = float(item.available_quantity) - demand.get(item.product_id, 0); reorder = max(float(item.reorder_level or 0), demand.get(item.product_id, 0) * 0.25); suggested = max(reorder - projected, 0)
        items.append({'inventory_id': item.id, 'product_id': item.product_id, 'product': item.product.name if item.product else None, 'available_quantity': float(item.available_quantity), 'forecast_demand': round(demand.get(item.product_id, 0), 2), 'projected_quantity': round(projected, 2), 'reorder_level': round(reorder, 2), 'suggested_order_quantity': round(suggested, 2), 'risk': 'Stockout risk' if projected < 0 else 'Watch' if projected <= reorder else 'Healthy'})
    return jsonify({'items': items, 'horizon_days': 30, 'method': 'Open production BOM demand plus reorder level', 'mode': 'api'})
