import base64
import json
import os
import urllib.parse
import urllib.request
from uuid import uuid4
from decimal import Decimal
from ..extensions import db
from ..models import Invoice, Payment, PaymentIntent, PaymentReconciliation


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
