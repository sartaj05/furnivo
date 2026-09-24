import os
from io import BytesIO
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ..extensions import db
from ..models import Invoice, PaymentIntent, PaymentOperation, PaymentReconciliation, QuoteClientAccess
from ..services.payments import create_checkout, payment_provider_status, request_provider_refund, settle_payment, verify_webhook_signature
from ..utils import current_user, roles_required

payments_bp = Blueprint('payments', __name__)


@payments_bp.get('/provider-status')
@roles_required('admin', 'sales')
def provider_status():
    return jsonify({'provider': payment_provider_status(), 'mode': 'api'})


@payments_bp.post('/invoices/<int:invoice_id>/checkout')
@roles_required('admin', 'sales', 'client')
def checkout(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    if current_user().role == 'client':
        access = db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == invoice.order.quote_id, QuoteClientAccess.user_id == current_user().id))
        if not access:
            return jsonify({'message': 'You do not have access to this invoice.'}), 403
    if invoice.balance <= 0:
        return jsonify({'message': 'This invoice is already paid.'}), 400
    idempotency_key = request.headers.get('Idempotency-Key') or f'checkout-{invoice.id}-{current_user().id}-{invoice.updated_at.timestamp()}'
    previous = db.session.scalar(db.select(PaymentOperation).where(PaymentOperation.operation_key == idempotency_key, PaymentOperation.operation_type == 'checkout'))
    if previous:
        intent = db.session.scalar(db.select(PaymentIntent).where(PaymentIntent.external_id == previous.external_id))
        if intent: return jsonify({'item': intent.to_dict(), 'mode': 'api', 'idempotent': True})
    try:
        intent = create_checkout(invoice)
    except Exception as exc:
        return jsonify({'message': f'Payment provider error: {exc}'}), 502
    db.session.add(PaymentOperation(operation_key=idempotency_key, operation_type='checkout', invoice_id=invoice.id, provider=intent.provider, external_id=intent.external_id, amount=intent.amount, status='created', message='Checkout created'))
    db.session.commit()
    return jsonify({'item': intent.to_dict(), 'mode': 'api'})


@payments_bp.post('/webhook/<provider>')
def webhook(provider):
    raw_body = request.get_data(cache=True)
    if not verify_webhook_signature(provider, raw_body, request.headers):
        return jsonify({'message': 'Invalid payment webhook signature.'}), 401
    payload = request.get_json(silent=True) or {}
    external_id = str(payload.get('external_id') or payload.get('payment_link_id') or payload.get('session_id') or '')
    if not external_id:
        return jsonify({'message': 'External payment id is required.'}), 400
    payment_status = str(payload.get('status', 'paid')).lower()
    reconciliation = db.session.scalar(db.select(PaymentReconciliation).where(PaymentReconciliation.external_id == external_id))
    if reconciliation and payment_status in {'failed', 'disputed', 'chargeback'}:
        reconciliation.status = 'Disputed' if payment_status in {'disputed', 'chargeback'} else 'Failed'; reconciliation.dispute_reason = str(payload.get('reason', payload.get('dispute_reason', 'Provider webhook update'))); db.session.commit()
        return jsonify({'item': reconciliation.to_dict(), 'provider': provider, 'mode': 'api'})
    invoice = settle_payment(external_id, payment_status)
    if not invoice:
        return jsonify({'message': 'Payment intent not found.'}), 404
    return jsonify({'item': invoice.to_dict(), 'provider': provider, 'mode': 'api'})


@payments_bp.post('/reconciliation/<int:reconciliation_id>/refund')
@roles_required('admin', 'sales')
def refund_reconciliation(reconciliation_id):
    item = db.get_or_404(PaymentReconciliation, reconciliation_id); payload = request.get_json(silent=True) or {}
    try: amount = Decimal(str(payload.get('amount', item.amount - item.refunded_amount)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Refund amount must be valid.'}), 400
    refundable = item.amount - item.refunded_amount
    if amount <= 0 or amount > refundable: return jsonify({'message': 'Refund amount exceeds the refundable balance.'}), 400
    idempotency_key = request.headers.get('Idempotency-Key') or str(payload.get('idempotency_key') or f'refund-{item.id}-{amount}')
    previous = db.session.scalar(db.select(PaymentOperation).where(PaymentOperation.operation_key == idempotency_key, PaymentOperation.operation_type == 'refund'))
    if previous: return jsonify({'item': item.to_dict(), 'operation': previous.to_dict(), 'mode': 'api', 'idempotent': True})
    try: provider_refund_id = request_provider_refund(item, amount)
    except Exception as exc: return jsonify({'message': f'Refund provider error: {exc}'}), 502
    item.refunded_amount += amount; item.refund_status = 'Refunded' if item.refunded_amount == item.amount else 'Partially refunded'; item.provider_refund_id = provider_refund_id; item.invoice.amount_paid = max(item.invoice.amount_paid - amount, 0); item.invoice.refresh_status()
    operation = PaymentOperation(operation_key=idempotency_key, operation_type='refund', invoice_id=item.invoice_id, reconciliation_id=item.id, provider=item.provider, external_id=provider_refund_id, amount=amount, status='completed', message='Refund completed')
    db.session.add(operation); db.session.commit()
    return jsonify({'item': item.to_dict(), 'operation': operation.to_dict(), 'invoice': item.invoice.to_dict(), 'mode': 'api'})


@payments_bp.get('/reconciliation/<int:reconciliation_id>/receipt')
@roles_required('admin', 'sales', 'client')
def refund_receipt(reconciliation_id):
    item = db.get_or_404(PaymentReconciliation, reconciliation_id)
    if current_user().role == 'client':
        access = db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == item.invoice.order.quote_id, QuoteClientAccess.user_id == current_user().id))
        if not access: return jsonify({'message': 'You do not have access to this receipt.'}), 403
    buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=A4); pdf.setFont('Helvetica-Bold', 18); pdf.drawString(48, 780, 'FURNIVO PAYMENT RECEIPT'); pdf.setFont('Helvetica', 11); pdf.drawString(48, 748, f'Invoice: {item.invoice.invoice_number}'); pdf.drawString(48, 728, f'Customer: {item.invoice.customer_name}'); pdf.drawString(48, 708, f'Provider: {item.provider}'); pdf.drawString(48, 688, f'Transaction: {item.external_id}'); pdf.drawString(48, 668, f'Amount received: INR {float(item.amount):,.2f}'); pdf.drawString(48, 648, f'Refunded: INR {float(item.refunded_amount):,.2f}'); pdf.drawString(48, 628, f'Status: {item.status} / {item.refund_status}'); pdf.save(); buffer.seek(0); return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'{item.invoice.invoice_number}-receipt.pdf')
