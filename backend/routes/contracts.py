from io import BytesIO
from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ..extensions import db
from ..models import Contract, ContractSignature, Quote, QuoteClientAccess
from ..services.audit import record_audit
from ..services.conversion import create_deposit_order_and_invoice
from ..utils import current_user, roles_required

contracts_bp = Blueprint('contracts', __name__)


def next_contract_number():
    numbers = []
    for value in db.session.scalars(db.select(Contract.contract_number)).all():
        try: numbers.append(int(str(value).split('-')[-1]))
        except ValueError: continue
    return f'CTR-{max(numbers, default=7000) + 1}'


def can_view(contract):
    if current_user().role != 'client': return True
    return bool(db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == contract.quote_id, QuoteClientAccess.user_id == current_user().id)))


@contracts_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_contracts():
    items = db.session.scalars(db.select(Contract).order_by(Contract.id.desc())).unique().all()
    return jsonify({'items': [item.to_dict() for item in items if can_view(item)], 'mode': 'api'})


@contracts_bp.post('')
@roles_required('admin', 'sales', 'designer')
def create_contract():
    payload = request.get_json(silent=True) or {}; quote = db.session.get(Quote, int(payload.get('quote_id'))) if payload.get('quote_id') else None
    if not quote: return jsonify({'message': 'Choose a valid quotation.'}), 400
    if db.session.scalar(db.select(Contract).where(Contract.quote_id == quote.id)): return jsonify({'message': 'A contract already exists for this quotation.'}), 409
    title = str(payload.get('title', '')).strip() or f'{quote.quote_number} - project agreement'
    terms = str(payload.get('terms', '')).strip()
    if not terms: return jsonify({'message': 'Contract terms are required.'}), 400
    item = Contract(contract_number=next_contract_number(), quote_id=quote.id, title=title, terms=terms, status='Sent', created_by_id=current_user().id)
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Contract created', 'contract', item.id, item.contract_number); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@contracts_bp.post('/<int:contract_id>/sign')
@roles_required('admin', 'sales', 'client')
def sign_contract(contract_id):
    item = db.get_or_404(Contract, contract_id)
    if not can_view(item): return jsonify({'message': 'You do not have access to this contract.'}), 403
    if item.status == 'Voided' or item.locked: return jsonify({'message': 'This contract is locked and cannot be signed again.'}), 400
    if item.quote.status != 'Approved': return jsonify({'message': 'The quotation must be approved before the contract can be signed.'}), 400
    payload = request.get_json(silent=True) or {}; signature_text = str(payload.get('signature_text', '')).strip()
    if len(signature_text) < 2: return jsonify({'message': 'Enter a valid signature name.'}), 400
    signature = ContractSignature(contract_id=item.id, signer_name=current_user().name, signer_email=current_user().email, signer_role=current_user().role, signature_text=signature_text, ip_address=request.headers.get('X-Forwarded-For', request.remote_addr or ''))
    item.status = 'Signed'; item.locked = True; item.signed_at = datetime.now(timezone.utc); db.session.add(signature)
    try:
        order, invoice, created = create_deposit_order_and_invoice(item.quote, current_user().id, current_app.config.get('DEFAULT_DEPOSIT_PERCENT', 30))
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400
    record_audit(current_user().id, 'Contract signed', 'contract', item.id, item.contract_number)
    db.session.commit()
    return jsonify({
        'item': item.to_dict(),
        'automation': {
            'order': order.to_dict() if order else None,
            'invoice': invoice.to_dict() if invoice else None,
            'created': created,
        },
        'mode': 'api',
    })


@contracts_bp.patch('/<int:contract_id>')
@roles_required('admin', 'sales')
def update_contract(contract_id):
    item = db.get_or_404(Contract, contract_id); payload = request.get_json(silent=True) or {}; status = str(payload.get('status', '')).strip()
    if item.locked: return jsonify({'message': 'Signed contracts are locked.'}), 400
    if status not in {'Draft', 'Sent', 'Voided'}: return jsonify({'message': 'Invalid contract status.'}), 400
    item.status = status; db.session.commit(); record_audit(current_user().id, 'Contract status changed', 'contract', item.id, status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@contracts_bp.get('/<int:contract_id>/pdf')
@roles_required('admin', 'sales', 'designer', 'client')
def contract_pdf(contract_id):
    item = db.get_or_404(Contract, contract_id)
    if not can_view(item): return jsonify({'message': 'You do not have access to this contract.'}), 403
    buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=A4); width, height = A4; y = height - 60
    pdf.setFont('Helvetica-Bold', 18); pdf.drawString(48, y, 'FURNIVO PROJECT AGREEMENT'); y -= 32
    pdf.setFont('Helvetica', 11); pdf.drawString(48, y, f'{item.contract_number} · {item.title}'); y -= 20; pdf.drawString(48, y, f'Quotation: {item.quote.quote_number} · Customer: {item.quote.customer_name}'); y -= 30
    pdf.setFont('Helvetica-Bold', 12); pdf.drawString(48, y, 'Terms and conditions'); y -= 20; pdf.setFont('Helvetica', 10)
    for paragraph in item.terms.splitlines() or ['']:
        for line in [paragraph[index:index + 100] for index in range(0, len(paragraph), 100)] or ['']:
            pdf.drawString(48, y, line); y -= 15
            if y < 80: pdf.showPage(); y = height - 60
    y -= 15; pdf.setFont('Helvetica-Bold', 12); pdf.drawString(48, y, 'Signatures'); y -= 20; pdf.setFont('Helvetica', 10)
    for signature in item.signatures: pdf.drawString(48, y, f'{signature.signer_name} ({signature.signer_role}) — {signature.signature_text} — {signature.signed_at.date().isoformat()}'); y -= 15
    pdf.save(); buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'{item.contract_number}.pdf')
