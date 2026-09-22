from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Product
from ..utils import current_user, roles_required

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
    include_archived = request.args.get('include_archived', '').lower() == 'true' and current_user().role == 'admin'
    query = db.select(Product).order_by(Product.name)
    if not include_archived: query = query.where(Product.is_active.is_(True))
    search = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    if search:
        like = f'%{search}%'
        query = query.where(or_(Product.name.ilike(like), Product.sku.ilike(like), Product.material.ilike(like)))
    if category:
        query = query.where(Product.category == category)
    try: page = max(int(request.args.get('page', 1)), 1); page_size = min(max(int(request.args.get('page_size', 50)), 1), 100)
    except ValueError: return jsonify({'message': 'page and page_size must be valid numbers.'}), 400
    total = db.session.scalar(db.select(db.func.count()).select_from(query.subquery())) or 0
    items = db.session.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'pagination': {'page': page, 'page_size': page_size, 'total': total, 'pages': (total + page_size - 1) // page_size}, 'mode': 'api'})


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

@products_bp.post('/<int:product_id>/variants')
@roles_required('admin')
def create_variant(product_id):
    from ..models import ProductVariant
    product = db.get_or_404(Product, product_id)
    payload = request.get_json(silent=True) or {}
    sku = str(payload.get('sku', '')).strip().upper()
    if not sku:
        return jsonify({'message': 'Variant SKU is required.'}), 400
    try:
        variant = ProductVariant(
            product=product,
            sku=sku,
            finish=str(payload.get('finish', 'Standard')).strip() or 'Standard',
            width_mm=int(payload['width_mm']) if payload.get('width_mm') else None,
            height_mm=int(payload['height_mm']) if payload.get('height_mm') else None,
            depth_mm=int(payload['depth_mm']) if payload.get('depth_mm') else None,
            price_delta=Decimal(str(payload.get('price_delta', 0) or 0)),
            stock_status=str(payload.get('stock_status', 'Made to order')).strip(),
        )
        db.session.add(variant)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Variant data is invalid or SKU already exists.'}), 400
    return jsonify({'item': variant.to_dict(), 'mode': 'api'}), 201


@products_bp.patch('/<int:product_id>/variants/<int:variant_id>')
@roles_required('admin')
def update_variant(product_id, variant_id):
    from ..models import ProductVariant
    variant = db.session.scalar(db.select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.product_id == product_id))
    if not variant:
        return jsonify({'message': 'Variant not found.'}), 404
    payload = request.get_json(silent=True) or {}
    for field in ['sku', 'finish', 'stock_status']:
        if field in payload:
            setattr(variant, field, str(payload[field]).strip())
    for field in ['width_mm', 'height_mm', 'depth_mm']:
        if field in payload:
            setattr(variant, field, int(payload[field]) if payload[field] else None)
    if 'price_delta' in payload:
        variant.price_delta = Decimal(str(payload['price_delta'] or 0))
    db.session.commit()
    return jsonify({'item': variant.to_dict(), 'mode': 'api'})


@products_bp.delete('/<int:product_id>/variants/<int:variant_id>')
@roles_required('admin')
def delete_variant(product_id, variant_id):
    from ..models import ProductVariant
    variant = db.session.scalar(db.select(ProductVariant).where(ProductVariant.id == variant_id, ProductVariant.product_id == product_id))
    if not variant:
        return jsonify({'message': 'Variant not found.'}), 404
    db.session.delete(variant)
    db.session.commit()
    return jsonify({'ok': True, 'mode': 'api'})
