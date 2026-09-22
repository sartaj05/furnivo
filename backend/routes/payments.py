import os
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Invoice, QuoteClientAccess
from ..services.payments import create_checkout, settle_payment
from ..utils import current_user, roles_required

payments_bp = Blueprint('payments', __name__)


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
    try:
        intent = create_checkout(invoice)
    except Exception as exc:
        return jsonify({'message': f'Payment provider error: {exc}'}), 502
    return jsonify({'item': intent.to_dict(), 'mode': 'api'})


@payments_bp.post('/webhook/<provider>')
def webhook(provider):
    secret = os.getenv('PAYMENT_WEBHOOK_SECRET', '')
    if secret and request.headers.get('X-Payment-Webhook-Secret') != secret:
        return jsonify({'message': 'Invalid webhook secret.'}), 401
    payload = request.get_json(silent=True) or {}
    external_id = str(payload.get('external_id') or payload.get('payment_link_id') or payload.get('session_id') or '')
    if not external_id:
        return jsonify({'message': 'External payment id is required.'}), 400
    invoice = settle_payment(external_id, str(payload.get('status', 'paid')).lower())
    if not invoice:
        return jsonify({'message': 'Payment intent not found.'}), 404
    return jsonify({'item': invoice.to_dict(), 'provider': provider, 'mode': 'api'})
