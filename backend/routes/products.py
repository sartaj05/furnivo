from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Product
from ..utils import roles_required

products_bp = Blueprint('products', __name__)


def product_from_payload(product, payload):
    required = ['sku', 'name', 'category']
    if any(not str(payload.get(field, getattr(product, field, ''))).strip() for field in required):
        raise ValueError('sku, name and category are required')

    product.sku = str(payload.get('sku', product.sku or '')).strip().upper()
    product.name = str(payload.get('name', product.name or '')).strip()
    product.category = str(payload.get('category', product.category or '')).strip()
    product.unit = str(payload.get('unit', product.unit or 'piece')).strip()
    product.material = str(payload.get('material', product.material or '')).strip()
    product.description = str(payload.get('description', product.description or '')).strip()
    product.image = str(payload.get('image', product.image or '')).strip()
    product.is_active = bool(payload.get('is_active', product.is_active if product.id else True))
    try:
        product.price = Decimal(str(payload.get('price', product.price or 0)))
    except (InvalidOperation, ValueError):
        raise ValueError('price must be a valid number')
    return product


@products_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_products():
    query = db.select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    if search:
        like = f'%{search}%'
        query = query.where(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.material.ilike(like)))
    if category:
        query = query.where(Product.category == category)
    items = db.session.scalars(query).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@products_bp.post('')
@roles_required('admin')
def create_product():
    payload = request.get_json(silent=True) or {}
    product = Product()
    try:
        product_from_payload(product, payload)
        db.session.add(product)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'SKU must be unique.'}), 409
    return jsonify({'item': product.to_dict(), 'mode': 'api'}), 201


@products_bp.patch('/<int:product_id>')
@roles_required('admin')
def update_product(product_id):
    product = db.get_or_404(Product, product_id)
    try:
        product_from_payload(product, request.get_json(silent=True) or {})
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'SKU must be unique.'}), 409
    return jsonify({'item': product.to_dict(), 'mode': 'api'})


@products_bp.delete('/<int:product_id>')
@roles_required('admin')
def delete_product(product_id):
    product = db.get_or_404(Product, product_id)
    product.is_active = False
    db.session.commit()
    return jsonify({'item': product.to_dict(), 'mode': 'api'})
