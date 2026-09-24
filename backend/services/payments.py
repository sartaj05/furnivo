import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from uuid import uuid4
from decimal import Decimal
from ..extensions import db
from ..models import Invoice, Payment, PaymentIntent, PaymentReconciliation
from .conversion import activate_order_after_payment


def payment_provider_status():
    provider = os.getenv('PAYMENT_PROVIDER', 'demo').lower()
    if provider == 'stripe':
        configured = bool(os.getenv('STRIPE_SECRET_KEY'))
        webhook_ready = bool(os.getenv('STRIPE_WEBHOOK_SECRET'))
        capabilities = ['checkout', 'refunds', 'webhooks']
    elif provider == 'razorpay':
        configured = bool(os.getenv('RAZORPAY_KEY_ID') and os.getenv('RAZORPAY_KEY_SECRET'))
        webhook_ready = bool(os.getenv('RAZORPAY_WEBHOOK_SECRET'))
        capabilities = ['payment_links', 'refunds', 'webhooks']
    else:
        configured = True
        webhook_ready = True
        capabilities = ['checkout', 'refunds', 'webhooks']
    return {'provider': provider, 'configured': configured, 'webhook_ready': webhook_ready, 'live_refunds': os.getenv('PAYMENT_LIVE_REFUNDS', 'false').lower() == 'true', 'capabilities': capabilities, 'mode': 'demo' if provider == 'demo' or not configured else 'live'}


def verify_webhook_signature(provider, raw_body, headers):
    """Verify provider webhooks before any payment state is changed."""
    provider = (provider or 'demo').lower()
    if provider == 'demo':
        secret = os.getenv('PAYMENT_WEBHOOK_SECRET', '')
        supplied = headers.get('X-Payment-Webhook-Secret', '')
        return not secret or hmac.compare_digest(supplied, secret)
    if provider == 'razorpay':
        secret = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
        supplied = headers.get('X-Razorpay-Signature', '')
        if not secret or not supplied:
            return False
        expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(supplied, expected)
    if provider == 'stripe':
        secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        signature = headers.get('Stripe-Signature', '')
        if not secret or not signature:
            return False
        parts = {}
        for item in signature.split(','):
            key, _, value = item.partition('=')
            parts.setdefault(key, []).append(value)
        try:
            timestamp = int(parts.get('t', ['0'])[0])
        except (TypeError, ValueError):
            return False
        if abs(time.time() - timestamp) > 300:
            return False
        expected = hmac.new(secret.encode(), f'{timestamp}.'.encode() + raw_body, hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(value, expected) for value in parts.get('v1', []))
    return False


def create_checkout(invoice):
    provider = os.getenv('PAYMENT_PROVIDER', 'demo').lower()
    amount = Decimal(str(invoice.balance))
    external_id = f'demo_{uuid4().hex}'
    checkout_url = f'/pay/{invoice.invoice_number}?intent={external_id}'
    if provider == 'stripe' and os.getenv('STRIPE_SECRET_KEY'):
        data = urllib.parse.urlencode({'mode': 'payment', 'success_url': os.getenv('PAYMENT_SUCCESS_URL', 'http://localhost:5173/#/app/invoices'), 'cancel_url': os.getenv('PAYMENT_CANCEL_URL', 'http://localhost:5173/#/app/invoices'), 'line_items[0][price_data][currency]': 'inr', 'line_items[0][price_data][product_data][name]': invoice.invoice_number, 'line_items[0][price_data][unit_amount]': int(amount * 100), 'line_items[0][quantity]': 1}).encode()
        request = urllib.request.Request('https://api.stripe.com/v1/checkout/sessions', data=data, headers={'Authorization': f"Bearer {os.getenv('STRIPE_SECRET_KEY')}", 'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode()); external_id = result['id']; checkout_url = result['url']
    elif provider == 'razorpay' and os.getenv('RAZORPAY_KEY_ID') and os.getenv('RAZORPAY_KEY_SECRET'):
        credentials = base64.b64encode(f"{os.getenv('RAZORPAY_KEY_ID')}:{os.getenv('RAZORPAY_KEY_SECRET')}".encode()).decode()
        payload = json.dumps({'amount': int(amount * 100), 'currency': 'INR', 'description': invoice.invoice_number, 'callback_url': os.getenv('PAYMENT_SUCCESS_URL', 'http://localhost:5173/#/app/invoices')}).encode()
        request = urllib.request.Request('https://api.razorpay.com/v1/payment_links', data=payload, headers={'Authorization': f'Basic {credentials}', 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode()); external_id = result['id']; checkout_url = result['short_url']
    intent = PaymentIntent(invoice_id=invoice.id, provider=provider, external_id=external_id, checkout_url=checkout_url, amount=amount)
    db.session.add(intent); db.session.commit()
    return intent


def settle_payment(external_id, status='paid'):
    intent = db.session.scalar(db.select(PaymentIntent).where(PaymentIntent.external_id == external_id))
    if not intent:
        return None
    intent.status = status
    invoice = intent.invoice
    if status == 'paid' and not db.session.scalar(db.select(Payment).where(Payment.reference == external_id)):
        invoice.amount_paid += intent.amount
        invoice.refresh_status()
        db.session.add(Payment(invoice_id=invoice.id, amount=intent.amount, method=intent.provider.title(), reference=external_id))
        activate_order_after_payment(invoice)
    db.session.commit()
    return invoice


def request_provider_refund(reconciliation, amount):
    provider = (reconciliation.provider or 'demo').lower()
    if os.getenv('PAYMENT_LIVE_REFUNDS', 'false').lower() != 'true' or provider in {'demo', 'manual', 'bank transfer'}:
        return f'demo_refund_{uuid4().hex}'
    if provider == 'stripe' and os.getenv('STRIPE_SECRET_KEY'):
        data = urllib.parse.urlencode({'payment_intent': reconciliation.external_id, 'amount': int(amount * 100)}).encode()
        request = urllib.request.Request('https://api.stripe.com/v1/refunds', data=data, headers={'Authorization': f"Bearer {os.getenv('STRIPE_SECRET_KEY')}", 'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response: return json.loads(response.read().decode())['id']
    if provider == 'razorpay' and os.getenv('RAZORPAY_KEY_ID') and os.getenv('RAZORPAY_KEY_SECRET'):
        credentials = base64.b64encode(f"{os.getenv('RAZORPAY_KEY_ID')}:{os.getenv('RAZORPAY_KEY_SECRET')}".encode()).decode()
        data = json.dumps({'amount': int(amount * 100), 'speed': 'normal'}).encode(); request = urllib.request.Request(f'https://api.razorpay.com/v1/payments/{reconciliation.external_id}/refund', data=data, headers={'Authorization': f'Basic {credentials}', 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response: return json.loads(response.read().decode())['id']
    raise RuntimeError('Live refund provider credentials are not configured.')
