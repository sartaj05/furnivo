from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Invoice, Order, Payment, QuoteClientAccess
from ..utils import current_user, roles_required

invoices_bp = Blueprint('invoices', __name__)


def next_invoice_number():
    numbers = []
    for value in db.session.scalars(db.select(Invoice.invoice_number)).all():
        try: numbers.append(int(str(value).split('-')[-1]))
        except ValueError: continue
    return f'INV-{max(numbers, default=2000) + 1}'


@invoices_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_invoices():
    query = db.select(Invoice).order_by(Invoice.id.desc())
    if current_user().role == 'client':
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()
        query = query.join(Invoice.order).where(Order.quote_id.in_(quote_ids or [-1]))
    items = db.session.scalars(query).unique().all()
    for item in items: item.refresh_status()
    db.session.commit()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@invoices_bp.post('')
@roles_required('admin', 'sales')
def create_invoice():
    payload = request.get_json(silent=True) or {}
    order = db.session.get(Order, int(payload.get('order_id'))) if payload.get('order_id') else None
    if not order:
        return jsonify({'message': 'Choose a valid order.'}), 400
    if db.session.scalar(db.select(Invoice).where(Invoice.order_id == order.id)):
        return jsonify({'message': 'An invoice already exists for this order.'}), 409
    invoice_number = next_invoice_number()
    invoice = Invoice(invoice_number=invoice_number, order_id=order.id, customer_id=order.customer_id, customer_name=order.customer_name, issue_date=date.today(), due_date=date.today() + timedelta(days=int(payload.get('due_days', 15) or 15)), status='Sent', subtotal=order.quote.subtotal, tax_amount=order.quote.tax_amount, total=order.quote.total, payment_link=f'/pay/{invoice_number}', notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
    db.session.add(invoice); db.session.commit()
    return jsonify({'item': invoice.to_dict(), 'mode': 'api'}), 201


@invoices_bp.post('/<int:invoice_id>/payments')
@roles_required('admin', 'sales')
def record_payment(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    payload = request.get_json(silent=True) or {}
    try: amount = Decimal(str(payload.get('amount', 0)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Payment amount must be valid.'}), 400
    if amount <= 0 or amount > invoice.balance:
        return jsonify({'message': 'Payment must be greater than zero and not exceed the balance.'}), 400
    payment = Payment(invoice_id=invoice.id, amount=amount, method=str(payload.get('method', 'Bank transfer')).strip(), reference=str(payload.get('reference', '')).strip())
    invoice.amount_paid += amount; db.session.add(payment); invoice.refresh_status(); db.session.commit()
    return jsonify({'item': invoice.to_dict(), 'mode': 'api'})
