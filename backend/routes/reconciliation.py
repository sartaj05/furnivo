from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Invoice, Payment, PaymentReconciliation, Order, QuoteClientAccess
from ..services.audit import record_audit
from ..utils import current_user, roles_required

reconciliation_bp = Blueprint('reconciliation', __name__)


def client_can_view(item):
    if current_user().role != 'client': return True
    return bool(db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == item.invoice.order.quote_id, QuoteClientAccess.user_id == current_user().id)))


@reconciliation_bp.get('')
@roles_required('admin', 'sales', 'client')
def list_reconciliations():
    items = db.session.scalars(db.select(PaymentReconciliation).order_by(PaymentReconciliation.id.desc())).unique().all()
    return jsonify({'items': [item.to_dict() for item in items if client_can_view(item)], 'mode': 'api'})


@reconciliation_bp.post('')
@roles_required('admin', 'sales')
def reconcile_payment():
    payload = request.get_json(silent=True) or {}
    invoice = db.session.get(Invoice, int(payload.get('invoice_id'))) if payload.get('invoice_id') else None
    if not invoice: return jsonify({'message': 'Choose a valid invoice.'}), 400
    external_id = str(payload.get('external_id', '')).strip()
    if not external_id: return jsonify({'message': 'Gateway transaction id is required.'}), 400
    if db.session.scalar(db.select(PaymentReconciliation).where(PaymentReconciliation.external_id == external_id)): return jsonify({'message': 'This transaction has already been reconciled.'}), 409
    status = str(payload.get('status', 'Paid')).strip()
    if status not in {'Paid', 'Failed', 'Disputed'}: return jsonify({'message': 'Invalid payment status.'}), 400
    try: amount = Decimal(str(payload.get('amount', 0)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Payment amount must be valid.'}), 400
    if amount <= 0: return jsonify({'message': 'Payment amount must be greater than zero.'}), 400
    if status == 'Paid' and amount > invoice.balance: return jsonify({'message': 'Payment exceeds the invoice balance.'}), 400
    item = PaymentReconciliation(invoice_id=invoice.id, provider=str(payload.get('provider', 'Manual')).strip() or 'Manual', external_id=external_id, amount=amount, status=status, dispute_reason=str(payload.get('dispute_reason', '')).strip())
    db.session.add(item)
    if status == 'Paid':
        invoice.amount_paid += amount; invoice.refresh_status(); db.session.add(Payment(invoice_id=invoice.id, amount=amount, method=item.provider, reference=external_id))
    db.session.commit(); record_audit(current_user().id, 'Payment reconciled', 'payment_reconciliation', item.id, f'{item.provider} / {status} / {amount}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@reconciliation_bp.post('/<int:reconciliation_id>/refund')
@roles_required('admin', 'sales')
def refund_payment(reconciliation_id):
    item = db.get_or_404(PaymentReconciliation, reconciliation_id); payload = request.get_json(silent=True) or {}
    try: amount = Decimal(str(payload.get('amount', item.amount - item.refunded_amount)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Refund amount must be valid.'}), 400
    refundable = item.amount - item.refunded_amount
    if amount <= 0 or amount > refundable: return jsonify({'message': 'Refund amount exceeds the refundable balance.'}), 400
    item.refunded_amount += amount; item.refund_status = 'Refunded' if item.refunded_amount == item.amount else 'Partially refunded'; item.provider_refund_id = str(payload.get('provider_refund_id') or f'refund_{item.id}_{int(item.refunded_amount)}')
    item.invoice.amount_paid = max(item.invoice.amount_paid - amount, 0); item.invoice.refresh_status()
    db.session.commit(); record_audit(current_user().id, 'Payment refund recorded', 'payment_reconciliation', item.id, f'{amount} / {item.provider_refund_id}'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'invoice': item.invoice.to_dict(), 'mode': 'api'})
