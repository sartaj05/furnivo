from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Product, ProductVariant, Quote, QuoteItem
from ..utils import current_user, roles_required

quotes_bp = Blueprint('quotes', __name__)


def next_quote_number():
    last_id = db.session.scalar(db.select(db.func.max(Quote.id))) or 0
    return f'Q-{1042 + last_id + 1}'


def build_item(payload):
    product_id = payload.get('product_id')
    variant_id = payload.get('variant_id') or None
    product = db.session.get(Product, int(product_id)) if product_id else None
    variant = db.session.get(ProductVariant, int(variant_id)) if variant_id else None

    description = str(payload.get('description') or (product.name if product else '')).strip()
    sku = str(payload.get('sku') or (variant.sku if variant else product.sku if product else '')).strip()
    unit = str(payload.get('unit') or (product.unit if product else 'piece')).strip()
    default_price = Decimal(str(product.price if product else 0)) + Decimal(str(variant.price_delta if variant else 0))
    try:
        quantity = Decimal(str(payload.get('quantity', 1)))
        unit_price = Decimal(str(payload.get('unit_price', default_price)))
    except InvalidOperation:
        raise ValueError('Quantity and unit price must be valid numbers.')
    if not description or quantity <= 0 or unit_price < 0:
        raise ValueError('Each line needs a description, positive quantity and valid price.')
    return QuoteItem(
        product_id=product.id if product else None,
        variant_id=variant.id if variant else None,
        description=description,
        sku=sku,
        quantity=quantity,
        unit=unit,
        unit_price=unit_price,
    )


@quotes_bp.get('')
@roles_required('admin', 'sales', 'designer')
def list_quotes():
    items = db.session.scalars(db.select(Quote).order_by(Quote.id.desc())).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@quotes_bp.get('/<int:quote_id>')
@roles_required('admin', 'sales', 'designer')
def get_quote(quote_id):
    quote = db.get_or_404(Quote, quote_id)
    return jsonify({'item': quote.to_dict(), 'mode': 'api'})


@quotes_bp.post('')
@roles_required('admin', 'sales', 'designer')
def create_quote():
    payload = request.get_json(silent=True) or {}
    customer = str(payload.get('customer', '')).strip()
    line_items = payload.get('items') or []
    if not customer or not line_items:
        return jsonify({'message': 'Customer and at least one quote line are required.'}), 400

    try:
        quote = Quote(
            quote_number=next_quote_number(),
            customer_name=customer,
            status='Draft',
            quote_date=date.today(),
            notes=str(payload.get('notes', '')).strip(),
            created_by_id=current_user().id,
        )
        quote.items = [build_item(item) for item in line_items]
        db.session.add(quote)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    return jsonify({'item': quote.to_dict(), 'mode': 'api'}), 201


@quotes_bp.patch('/<int:quote_id>/status')
@roles_required('admin', 'sales')
def update_quote_status(quote_id):
    quote = db.get_or_404(Quote, quote_id)
    status = str((request.get_json(silent=True) or {}).get('status', '')).strip()
    if status not in {'Draft', 'Sent', 'Approved', 'Rejected'}:
        return jsonify({'message': 'Invalid quote status.'}), 400
    quote.status = status
    db.session.commit()
    return jsonify({'item': quote.to_dict(), 'mode': 'api'})

@quotes_bp.get('/<int:quote_id>/pdf')
@roles_required('admin', 'sales', 'designer')
def quote_pdf(quote_id):
    from flask import send_file
    from ..services.quote_pdf import build_quote_pdf
    quote = db.get_or_404(Quote, quote_id)
    return send_file(
        build_quote_pdf(quote),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{quote.quote_number}.pdf',
    )
