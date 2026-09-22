from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Product, PurchaseOrder, PurchaseOrderItem, Supplier
from ..utils import current_user, roles_required

procurement_bp = Blueprint('procurement', __name__)


def next_po_number():
    numbers = []
    for value in db.session.scalars(db.select(PurchaseOrder.po_number)).all():
        try: numbers.append(int(str(value).split('-')[-1]))
        except ValueError: continue
    return f'PO-{max(numbers, default=3000) + 1}'


@procurement_bp.get('/suppliers')
@roles_required('admin', 'sales', 'designer')
def list_suppliers():
    items = db.session.scalars(db.select(Supplier).where(Supplier.is_active.is_(True)).order_by(Supplier.name)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@procurement_bp.post('/suppliers')
@roles_required('admin')
def create_supplier():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    if not name: return jsonify({'message': 'Supplier name is required.'}), 400
    if db.session.scalar(db.select(Supplier).where(Supplier.name == name)): return jsonify({'message': 'Supplier already exists.'}), 409
    item = Supplier(name=name, email=str(payload.get('email', '')).strip(), phone=str(payload.get('phone', '')).strip(), notes=str(payload.get('notes', '')).strip())
    db.session.add(item); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@procurement_bp.get('/purchase-orders')
@roles_required('admin', 'sales', 'designer')
def list_purchase_orders():
    items = db.session.scalars(db.select(PurchaseOrder).order_by(PurchaseOrder.id.desc())).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@procurement_bp.post('/purchase-orders')
@roles_required('admin', 'sales')
def create_purchase_order():
    payload = request.get_json(silent=True) or {}
    supplier = db.session.get(Supplier, int(payload.get('supplier_id'))) if payload.get('supplier_id') else None
    items = payload.get('items') or []
    if not supplier or not items: return jsonify({'message': 'Supplier and at least one item are required.'}), 400
    try:
        po = PurchaseOrder(po_number=next_po_number(), supplier_id=supplier.id, status='Draft', order_date=date.today(), expected_date=date.fromisoformat(payload['expected_date']) if payload.get('expected_date') else None, notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
        for row in items:
            product = db.session.get(Product, int(row.get('product_id'))) if row.get('product_id') else None
            if not product: raise ValueError('Each purchase item needs a valid product.')
            quantity = Decimal(str(row.get('quantity', 0))); unit_cost = Decimal(str(row.get('unit_cost', 0)))
            if quantity <= 0 or unit_cost < 0: raise ValueError('Purchase quantity and cost are invalid.')
            po.items.append(PurchaseOrderItem(product_id=product.id, description=product.name, quantity=quantity, unit_cost=unit_cost))
        db.session.add(po); db.session.commit()
    except (ValueError, InvalidOperation) as exc:
        db.session.rollback(); return jsonify({'message': str(exc)}), 400
    return jsonify({'item': po.to_dict(), 'mode': 'api'}), 201


@procurement_bp.patch('/purchase-orders/<int:po_id>')
@roles_required('admin', 'sales')
def update_purchase_order(po_id):
    item = db.get_or_404(PurchaseOrder, po_id); payload = request.get_json(silent=True) or {}
    if 'status' in payload: item.status = str(payload['status']).strip()
    if 'expected_date' in payload: item.expected_date = date.fromisoformat(payload['expected_date']) if payload['expected_date'] else None
    db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'})
