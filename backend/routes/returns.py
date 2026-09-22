from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import CreditNote, Invoice, Order, ReturnRequest, QuoteClientAccess
from ..services.audit import record_audit
from ..utils import current_user, roles_required

returns_bp = Blueprint('returns', __name__)


def next_credit_note():
    numbers = []
    for value in db.session.scalars(db.select(CreditNote.credit_note_number)).all():
        try: numbers.append(int(str(value).split('-')[-1]))
        except ValueError: continue
    return f'CN-{max(numbers, default=4000) + 1}'


@returns_bp.get('')
@roles_required('admin', 'sales', 'client')
def list_returns():
    query = db.select(ReturnRequest).order_by(ReturnRequest.id.desc())
    if current_user().role == 'client':
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()
        query = query.join(ReturnRequest.order).where(Order.quote_id.in_(quote_ids or [-1]))
    items = db.session.scalars(query).unique().all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@returns_bp.post('')
@roles_required('admin', 'sales', 'client')
def create_return():
    payload = request.get_json(silent=True) or {}
    order = db.session.get(Order, int(payload.get('order_id'))) if payload.get('order_id') else None
    if not order: return jsonify({'message': 'Choose a valid order.'}), 400
    if current_user().role == 'client':
        access = db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == order.quote_id, QuoteClientAccess.user_id == current_user().id))
        if not access: return jsonify({'message': 'You do not have access to this order.'}), 403
    try: amount = Decimal(str(payload.get('amount', 0)))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Refund amount must be valid.'}), 400
    if amount <= 0 or amount > order.quote.total: return jsonify({'message': 'Refund amount is outside the order total.'}), 400
    item = ReturnRequest(order_id=order.id, invoice_id=payload.get('invoice_id') or None, customer_name=order.customer_name, reason=str(payload.get('reason', '')).strip(), amount=amount, status='Requested', notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
    if not item.reason: return jsonify({'message': 'Return reason is required.'}), 400
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Return requested', 'return', item.id, item.reason); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@returns_bp.patch('/<int:return_id>')
@roles_required('admin', 'sales')
def update_return(return_id):
    item = db.get_or_404(ReturnRequest, return_id); payload = request.get_json(silent=True) or {}; status = str(payload.get('status', '')).strip()
    if status not in {'Requested', 'Approved', 'Rejected', 'Refunded'}: return jsonify({'message': 'Invalid return status.'}), 400
    item.status = status
    if status == 'Approved' and not item.credit_note:
        db.session.add(CreditNote(credit_note_number=next_credit_note(), return_request_id=item.id, amount=item.amount, status='Issued'))
    db.session.commit(); record_audit(current_user().id, f'Return {status.lower()}', 'return', item.id, item.customer_name); db.session.commit(); return jsonify({'item': item.to_dict(), 'mode': 'api'})
