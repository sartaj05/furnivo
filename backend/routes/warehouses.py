from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Product, StockMovement, Warehouse, WarehouseStock
from ..services.audit import record_audit
from ..utils import current_user, roles_required

warehouses_bp = Blueprint('warehouses', __name__)


@warehouses_bp.get('')
@roles_required('admin', 'sales', 'designer')
def list_warehouses():
    return jsonify({'items': [item.to_dict() for item in db.session.scalars(db.select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.name)).all()], 'mode': 'api'})


@warehouses_bp.post('')
@roles_required('admin')
def create_warehouse():
    payload = request.get_json(silent=True) or {}; name = str(payload.get('name', '')).strip()
    if not name: return jsonify({'message': 'Warehouse name is required.'}), 400
    item = Warehouse(name=name, address=str(payload.get('address', '')).strip(), manager=str(payload.get('manager', '')).strip())
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Warehouse created', 'warehouse', item.id, item.name); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@warehouses_bp.get('/stock')
@roles_required('admin', 'sales', 'designer')
def list_stock():
    items = db.session.scalars(db.select(WarehouseStock).order_by(WarehouseStock.warehouse_id, WarehouseStock.id)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@warehouses_bp.get('/movements')
@roles_required('admin', 'sales', 'designer')
def list_movements():
    items = db.session.scalars(db.select(StockMovement).order_by(StockMovement.id.desc()).limit(100)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@warehouses_bp.post('/transfer')
@roles_required('admin', 'sales')
def transfer_stock():
    payload = request.get_json(silent=True) or {}
    try: quantity = Decimal(str(payload.get('quantity', 0)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Transfer quantity must be valid.'}), 400
    if quantity <= 0: return jsonify({'message': 'Transfer quantity must be greater than zero.'}), 400
    source = db.session.scalar(db.select(WarehouseStock).where(WarehouseStock.warehouse_id == int(payload.get('from_warehouse_id')), WarehouseStock.product_id == int(payload.get('product_id'))))
    if not source or source.quantity - source.reserved_quantity < quantity: return jsonify({'message': 'Not enough available stock in source warehouse.'}), 400
    target = db.session.scalar(db.select(WarehouseStock).where(WarehouseStock.warehouse_id == int(payload.get('to_warehouse_id')), WarehouseStock.product_id == int(payload.get('product_id'))))
    if not target:
        target = WarehouseStock(warehouse_id=int(payload['to_warehouse_id']), product_id=int(payload['product_id']), quantity=0, reserved_quantity=0); db.session.add(target)
    source.quantity -= quantity; target.quantity += quantity
    movement = StockMovement(from_warehouse_id=source.warehouse_id, to_warehouse_id=target.warehouse_id, product_id=source.product_id, quantity=quantity, movement_type='Transfer', reference=str(payload.get('reference', '')).strip(), created_by_id=current_user().id)
    db.session.add(movement); db.session.commit(); record_audit(current_user().id, 'Stock transferred', 'warehouse', movement.id, f'{quantity} units'); db.session.commit()
    return jsonify({'item': movement.to_dict(), 'mode': 'api'}), 201
