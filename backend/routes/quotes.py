from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Customer, FurnitureConfiguration, Order, Product, ProductVariant, Quote, QuoteClientAccess, QuoteItem, QuoteRevision
from ..utils import assigned_order_ids, current_user, roles_required
from ..services.notifications import create_notification, notify_quote_client
from ..services.audit import record_audit
from ..services.conversion import ensure_contract_for_approved_quote

quotes_bp = Blueprint('quotes', __name__)


def record_revision(quote, action, comment=''):
    latest = db.session.scalar(
        db.select(db.func.max(QuoteRevision.version)).where(QuoteRevision.quote_id == quote.id)
    ) or 0
    revision = QuoteRevision(
        quote_id=quote.id,
        version=latest + 1,
        action=action,
        status=quote.status,
        subtotal=quote.subtotal,
        amount=quote.total,
        comment=comment,
        changed_by_id=current_user().id if current_user() else None,
    )
    db.session.add(revision)


def next_quote_number():
    numbers = []
    for value in db.session.scalars(db.select(Quote.quote_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f"Q-{max(numbers, default=1041) + 1}"


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
    query = db.select(Quote).order_by(Quote.id.desc())
    if current_user().role in {'sales', 'designer'}:
        assigned_quotes = db.select(Order.quote_id).where(Order.id.in_(assigned_order_ids() or [-1]))
        query = query.where(or_(Quote.created_by_id == current_user().id, Quote.id.in_(assigned_quotes)))
    items = db.session.scalars(query).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@quotes_bp.get('/client')
@roles_required('client')
def list_client_quotes():
    accesses = db.session.scalars(
        db.select(QuoteClientAccess).where(QuoteClientAccess.user_id == current_user().id).order_by(QuoteClientAccess.id.desc())
    ).all()
    items = []
    for access in accesses:
        item = access.quote.to_dict()
        item['client_access'] = access.to_dict()
        items.append(item)
    return jsonify({'items': items, 'mode': 'api'})


@quotes_bp.get('/<int:quote_id>')
@roles_required('admin', 'sales', 'designer')
def get_quote(quote_id):
    quote = db.get_or_404(Quote, quote_id)
    return jsonify({'item': quote.to_dict(), 'mode': 'api'})


@quotes_bp.post('')
@roles_required('admin', 'sales', 'designer')
def create_quote():
    payload = request.get_json(silent=True) or {}
    customer_id = payload.get('customer_id') or None
    customer_record = db.session.get(Customer, int(customer_id)) if customer_id else None
    customer = str(payload.get('customer') or (customer_record.company if customer_record else '')).strip()
    configuration = None
    configuration_id = payload.get('configuration_id')
    if configuration_id:
        configuration = db.session.get(FurnitureConfiguration, int(configuration_id))
        if not configuration:
            return jsonify({'message': 'Furniture configuration was not found.'}), 404
        line_items = configuration.items
        if not customer_record and configuration.customer_id:
            customer_record = db.session.get(Customer, configuration.customer_id)
            customer = customer_record.company if customer_record else customer
    else:
        line_items = payload.get('items') or []
    if not customer or not line_items:
        return jsonify({'message': 'Customer and at least one quote line are required.'}), 400

    try:
        quote = Quote(
            quote_number=next_quote_number(),
            customer_name=customer,
            customer_id=customer_record.id if customer_record else None,
            status='Draft',
            quote_date=date.today(),
            notes=str(payload.get('notes', '')).strip(),
            discount_percent=Decimal(str(payload.get('discount_percent', 0) or 0)),
            tax_percent=Decimal(str(payload.get('tax_percent', 18) or 0)),
            shipping_amount=Decimal(str(payload.get('shipping_amount', 0) or 0)),
            created_by_id=current_user().id,
        )
        quote.items = [build_item(item) for item in line_items]
        db.session.add(quote)
        db.session.commit()
        if configuration:
            configuration.quote_id = quote.id
            configuration.status = 'Quoted'
            db.session.commit()
        record_revision(quote, 'Created')
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
    if status not in {'Draft', 'Sent', 'Approved', 'Rejected', 'Change Requested'}:
        return jsonify({'message': 'Invalid quote status.'}), 400
    quote.status = status
    record_revision(quote, f'Status changed to {status}')
    record_audit(current_user().id, f'Quote status changed to {status}', 'quote', quote.id, quote.quote_number)
    notify_quote_client(quote, 'Quotation updated', f'{quote.quote_number} is now {status}.', 'quote')
    db.session.commit()
    return jsonify({'item': quote.to_dict(), 'mode': 'api'})


@quotes_bp.get('/<int:quote_id>/history')
@roles_required('admin', 'sales', 'designer', 'client')
def quote_history(quote_id):
    quote = db.get_or_404(Quote, quote_id)
    if current_user().role == 'client':
        access = db.session.scalar(db.select(QuoteClientAccess).where(
            QuoteClientAccess.quote_id == quote.id,
            QuoteClientAccess.user_id == current_user().id,
        ))
        if not access:
            return jsonify({'message': 'You do not have access to this quotation.'}), 403
    revisions = db.session.scalars(
        db.select(QuoteRevision).where(QuoteRevision.quote_id == quote.id).order_by(QuoteRevision.version.desc())
    ).all()
    return jsonify({'items': [revision.to_dict() for revision in revisions], 'mode': 'api'})

@quotes_bp.get('/<int:quote_id>/pdf')
@roles_required('admin', 'sales', 'designer', 'client')
def quote_pdf(quote_id):
    from flask import send_file
    from ..services.quote_pdf import build_quote_pdf
    quote = db.get_or_404(Quote, quote_id)
    if current_user().role == 'client':
        access = db.session.scalar(db.select(QuoteClientAccess).where(
            QuoteClientAccess.quote_id == quote.id,
            QuoteClientAccess.user_id == current_user().id,
        ))
        if not access:
            return jsonify({'message': 'You do not have access to this quotation.'}), 403
    return send_file(
        build_quote_pdf(quote),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{quote.quote_number}.pdf',
    )


@quotes_bp.post('/<int:quote_id>/client-response')
@roles_required('client')
def client_response(quote_id):
    access = db.session.scalar(db.select(QuoteClientAccess).where(
        QuoteClientAccess.quote_id == quote_id,
        QuoteClientAccess.user_id == current_user().id,
    ))
    if not access:
        return jsonify({'message': 'You do not have access to this quotation.'}), 403
    payload = request.get_json(silent=True) or {}
    action = str(payload.get('action', '')).strip()
    comment = str(payload.get('comment', '')).strip()
    if action not in {'Approved', 'Rejected', 'Change Requested'}:
        return jsonify({'message': 'Choose approve, reject or request changes.'}), 400
    if action == 'Change Requested' and not comment:
        return jsonify({'message': 'Add a comment when requesting changes.'}), 400
    access.last_action = action
    access.response_comment = comment
    access.responded_at = datetime.now(timezone.utc)
    access.quote.status = action
    contract = None
    contract_created = False
    if action == 'Approved':
        contract, contract_created = ensure_contract_for_approved_quote(access.quote, current_user().id)
    record_revision(access.quote, f'Client {action}', comment)
    record_audit(current_user().id, f'Client {action}', 'quote', access.quote.id, comment)
    create_notification(access.quote.created_by_id, 'Client response received', f'{access.quote.quote_number}: {action}.', 'quote', 'quote', access.quote.id)
    db.session.commit()
    item = access.quote.to_dict()
    item['client_access'] = access.to_dict()
    return jsonify({
        'item': item,
        'automation': {
            'contract': contract.to_dict() if contract else None,
            'contract_created': contract_created,
        },
        'mode': 'api',
    })
