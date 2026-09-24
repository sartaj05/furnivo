import base64
import hashlib
import hmac
import time
from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, current_app, jsonify, request
from ..extensions import db
from ..models import Product, PurchaseOrder, PurchaseOrderItem, Supplier
from ..utils import current_user, roles_required
from ..services.audit import record_audit

procurement_bp = Blueprint('procurement', __name__)


def supplier_portal_token(supplier_id):
    expires = int(time.time()) + 7 * 86400
    value = f'{supplier_id}:{expires}'
    signature = hmac.new(str(current_app.config['SECRET_KEY']).encode(), value.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f'{value}:{signature}'.encode()).decode().rstrip('=')


def supplier_from_token(token):
    try:
        raw = base64.urlsafe_b64decode(str(token) + '=' * (-len(str(token)) % 4)).decode()
        supplier_id, expires, signature = raw.split(':', 2)
        value = f'{supplier_id}:{expires}'
        expected = hmac.new(str(current_app.config['SECRET_KEY']).encode(), value.encode(), hashlib.sha256).hexdigest()[:32]
        if int(expires) < int(time.time()) or not hmac.compare_digest(signature, expected): return None
        return db.session.get(Supplier, int(supplier_id))
    except (ValueError, TypeError, UnicodeDecodeError): return None


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
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Supplier created', 'supplier', item.id, item.name); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


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
        po = PurchaseOrder(po_number=next_po_number(), supplier_id=supplier.id, status='Draft', order_date=date.today(), expected_date=date.fromisoformat(payload['expected_date']) if payload.get('expected_date') else None, supplier_quote_ref=str(payload.get('supplier_quote_ref', '')).strip(), notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
        for row in items:
            product = db.session.get(Product, int(row.get('product_id'))) if row.get('product_id') else None
            if not product: raise ValueError('Each purchase item needs a valid product.')
            quantity = Decimal(str(row.get('quantity', 0))); unit_cost = Decimal(str(row.get('unit_cost', 0)))
            if quantity <= 0 or unit_cost < 0: raise ValueError('Purchase quantity and cost are invalid.')
            po.items.append(PurchaseOrderItem(product_id=product.id, description=product.name, quantity=quantity, unit_cost=unit_cost))
        db.session.add(po); db.session.commit()
        record_audit(current_user().id, 'Purchase order created', 'purchase_order', po.id, po.po_number); db.session.commit()
    except (ValueError, InvalidOperation) as exc:
        db.session.rollback(); return jsonify({'message': str(exc)}), 400
    return jsonify({'item': po.to_dict(), 'mode': 'api'}), 201


@procurement_bp.patch('/purchase-orders/<int:po_id>')
@roles_required('admin', 'sales')
def update_purchase_order(po_id):
    item = db.get_or_404(PurchaseOrder, po_id); payload = request.get_json(silent=True) or {}
    if 'status' in payload: item.status = str(payload['status']).strip()
    if 'expected_date' in payload: item.expected_date = date.fromisoformat(payload['expected_date']) if payload['expected_date'] else None
    if 'actual_delivery_date' in payload: item.actual_delivery_date = date.fromisoformat(payload['actual_delivery_date']) if payload['actual_delivery_date'] else None
    if 'supplier_quote_ref' in payload: item.supplier_quote_ref = str(payload['supplier_quote_ref']).strip()
    if 'landed_cost' in payload: item.landed_cost = Decimal(str(payload['landed_cost'] or 0))
    if 'quality_rating' in payload: item.quality_rating = Decimal(str(payload['quality_rating'] or 0))
    db.session.commit(); record_audit(current_user().id, 'Purchase order updated', 'purchase_order', item.id, item.po_number); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'})


@procurement_bp.post('/purchase-orders/from-planning')
@roles_required('admin', 'sales')
def create_purchase_order_from_planning():
    payload = request.get_json(silent=True) or {}; suggestions = payload.get('items') or []
    supplier = db.session.get(Supplier, int(payload.get('supplier_id'))) if payload.get('supplier_id') else None
    if not supplier or not suggestions: return jsonify({'message': 'Supplier and planning suggestions are required.'}), 400
    try:
        po = PurchaseOrder(po_number=next_po_number(), supplier_id=supplier.id, status='Draft', order_date=date.today(), expected_date=date.fromisoformat(payload['expected_date']) if payload.get('expected_date') else None, supplier_quote_ref=str(payload.get('supplier_quote_ref', '')).strip(), notes=str(payload.get('notes', 'Created from production planning shortages.')).strip(), created_by_id=current_user().id)
        for row in suggestions:
            product = db.session.get(Product, int(row.get('product_id'))) if row.get('product_id') else None
            quantity = Decimal(str(row.get('quantity', row.get('shortage_quantity', 0))))
            unit_cost = Decimal(str(row.get('unit_cost', 0)))
            if not product or quantity <= 0 or unit_cost < 0: raise ValueError('Every planning item needs a valid product, quantity, and cost.')
            po.items.append(PurchaseOrderItem(product_id=product.id, description=product.name, quantity=quantity, unit_cost=unit_cost))
        db.session.add(po); db.session.commit(); record_audit(current_user().id, 'Purchase order created from planning', 'purchase_order', po.id, po.po_number); db.session.commit()
    except (ValueError, InvalidOperation) as exc:
        db.session.rollback(); return jsonify({'message': str(exc)}), 400
    return jsonify({'item': po.to_dict(), 'mode': 'api'}), 201


@procurement_bp.get('/supplier-performance')
@roles_required('admin', 'sales', 'designer')
def supplier_performance():
    suppliers = db.session.scalars(db.select(Supplier).order_by(Supplier.name)).all()
    items = []
    for supplier in suppliers:
        orders = db.session.scalars(db.select(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier.id)).all()
        delivered = [po for po in orders if po.actual_delivery_date]
        ratings = [float(po.quality_rating or 0) for po in orders if po.quality_rating]
        items.append({'supplier_id': supplier.id, 'supplier': supplier.name, 'orders': len(orders), 'received': sum(po.status == 'Received' for po in orders), 'on_time_rate': round(sum(po.actual_delivery_date <= po.expected_date for po in delivered if po.expected_date) / max(sum(bool(po.expected_date) for po in delivered), 1) * 100, 1), 'quality_rating': round(sum(ratings) / len(ratings), 1) if ratings else 0})
    return jsonify({'items': items, 'mode': 'api'})


@procurement_bp.post('/supplier-portal/invites')
@roles_required('admin')
def create_supplier_portal_invite():
    payload = request.get_json(silent=True) or {}
    supplier = db.session.get(Supplier, int(payload.get('supplier_id'))) if payload.get('supplier_id') else None
    if not supplier: return jsonify({'message': 'Supplier not found.'}), 404
    return jsonify({'supplier': supplier.to_dict(), 'token': supplier_portal_token(supplier.id), 'expires_in_days': 7, 'mode': 'api'}), 201


@procurement_bp.get('/supplier-portal/<token>')
def supplier_portal(token):
    supplier = supplier_from_token(token)
    if not supplier: return jsonify({'message': 'Supplier portal link is invalid or expired.'}), 401
    orders = db.session.scalars(db.select(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier.id).order_by(PurchaseOrder.id.desc())).unique().all()
    return jsonify({'supplier': supplier.to_dict(), 'purchase_orders': [item.to_dict() for item in orders], 'mode': 'api'})


@procurement_bp.patch('/supplier-portal/<token>/purchase-orders/<int:po_id>')
def supplier_portal_update(token, po_id):
    supplier = supplier_from_token(token); item = db.session.get(PurchaseOrder, po_id)
    if not supplier: return jsonify({'message': 'Supplier portal link is invalid or expired.'}), 401
    if not item or item.supplier_id != supplier.id: return jsonify({'message': 'Purchase order not found for this supplier.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'status' in payload and str(payload['status']) in {'Confirmed', 'In transit', 'Received'}: item.status = str(payload['status'])
    if 'expected_date' in payload: item.expected_date = date.fromisoformat(payload['expected_date']) if payload['expected_date'] else None
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
