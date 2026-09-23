from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from ..extensions import db
from ..models import Contract, Invoice, Order
from .audit import record_audit
from .notifications import notify_quote_client, notify_roles


DEFAULT_CONTRACT_TERMS = (
    '1. Furnivo will deliver the approved scope and materials listed in the quotation.\n'
    '2. Production begins after written approval and the agreed advance payment.\n'
    '3. Delivery and installation dates are scheduled after material confirmation.\n'
    '4. Variations require written approval and may change price or timeline.'
)


def next_contract_number():
    numbers = []
    for value in db.session.scalars(db.select(Contract.contract_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f'CTR-{max(numbers, default=7000) + 1}'


def next_invoice_number():
    numbers = []
    for value in db.session.scalars(db.select(Invoice.invoice_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f'INV-{max(numbers, default=2000) + 1}'


def ensure_contract_for_approved_quote(quote, actor_id=None):
    contract = db.session.scalar(db.select(Contract).where(Contract.quote_id == quote.id))
    if contract:
        return contract, False
    contract = Contract(
        contract_number=next_contract_number(),
        quote_id=quote.id,
        title=f'{quote.quote_number} - project agreement',
        terms=DEFAULT_CONTRACT_TERMS,
        status='Sent',
        created_by_id=quote.created_by_id,
    )
    db.session.add(contract)
    db.session.flush()
    record_audit(actor_id, 'Approval contract created', 'contract', contract.id, contract.contract_number)
    notify_quote_client(quote, 'Agreement ready to sign', f'{quote.quote_number} was approved. Please review and sign the project agreement.', 'contract')
    return contract, True


def create_deposit_order_and_invoice(quote, actor_id=None, deposit_percent=30):
    """Create the provisional order and deposit invoice once a contract is signed.

    The operation is intentionally idempotent: a quote can be retried after a
    timeout without creating a second order or invoice.
    """
    existing_order = db.session.scalar(db.select(Order).where(Order.quote_id == quote.id))
    if existing_order:
        existing_invoice = db.session.scalar(db.select(Invoice).where(Invoice.order_id == existing_order.id))
        return existing_order, existing_invoice, False

    try:
        deposit_percent = Decimal(str(deposit_percent or 30))
    except Exception as exc:
        raise ValueError('Deposit percentage must be a valid number.') from exc
    deposit_percent = min(max(deposit_percent, Decimal('1')), Decimal('100'))
    total = Decimal(str(quote.total or 0))
    deposit_total = (total * deposit_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if deposit_total <= 0:
        raise ValueError('A deposit invoice cannot be created for a zero-value quotation.')

    order = Order(
        order_number=_next_order_number(),
        quote_id=quote.id,
        customer_id=quote.customer_id,
        customer_name=quote.customer_name,
        status='Awaiting deposit',
        production_status='Not started',
        installation_status='Not scheduled',
        notes=f'Automatically created after signed contract. Deposit required: {deposit_percent}%.',
        created_by_id=quote.created_by_id,
    )
    db.session.add(order)
    db.session.flush()

    invoice_number = next_invoice_number()
    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.id,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=7),
        status='Sent',
        invoice_type='Deposit',
        deposit_percent=deposit_percent,
        subtotal=(Decimal(str(quote.subtotal or 0)) * deposit_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        tax_amount=(Decimal(str(quote.tax_amount or 0)) * deposit_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        total=deposit_total,
        payment_link=f'/pay/{invoice_number}',
        notes=f'{deposit_percent}% advance payment for {quote.quote_number}. The final balance will be invoiced separately.',
        created_by_id=quote.created_by_id,
    )
    db.session.add(invoice)
    record_audit(actor_id, 'Deposit order and invoice created', 'order', order.id, f'{order.order_number} / {invoice.invoice_number}')
    notify_quote_client(quote, 'Deposit invoice ready', f'{invoice.invoice_number} is ready for your {deposit_percent}% advance payment.', 'invoice')
    notify_roles(['admin', 'sales'], 'Signed contract ready for deposit', f'{quote.quote_number} has a signed contract and is awaiting deposit payment.', 'order')
    return order, invoice, True


def activate_order_after_payment(invoice):
    """Move an awaiting-deposit order into confirmed status exactly once."""
    order = invoice.order
    if not order or order.status != 'Awaiting deposit' or invoice.balance > 0:
        return False
    order.status = 'Confirmed'
    order.notes = f'{order.notes} Deposit paid; project released for production.'.strip()
    record_audit(None, 'Deposit paid; order activated', 'order', order.id, order.order_number)
    notify_quote_client(order.quote, 'Deposit received', f'{invoice.invoice_number} is paid. {order.order_number} is now confirmed.', 'payment')
    notify_roles(['admin', 'sales'], 'Deposit received', f'{order.order_number} is confirmed and ready for production planning.', 'payment')
    return True


def _next_order_number():
    numbers = []
    for value in db.session.scalars(db.select(Order.order_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f'ORD-{max(numbers, default=1000) + 1}'
