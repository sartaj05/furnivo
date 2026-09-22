import json
from decimal import Decimal
from uuid import uuid4
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import EInvoice, Invoice, QuoteClientAccess
from ..services.audit import record_audit
from ..utils import current_user, roles_required

gst_bp = Blueprint('gst', __name__)


def client_can_view(item):
    if current_user().role != 'client': return True
    return bool(db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == item.invoice.order.quote_id, QuoteClientAccess.user_id == current_user().id)))


@gst_bp.get('')
@roles_required('admin', 'sales', 'client')
def list_einvoices():
    items = db.session.scalars(db.select(EInvoice).order_by(EInvoice.id.desc())).unique().all()
    return jsonify({'items': [item.to_dict() for item in items if client_can_view(item)], 'mode': 'api'})


@gst_bp.post('/invoices/<int:invoice_id>/generate')
@roles_required('admin', 'sales')
def generate_einvoice(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id); existing = db.session.scalar(db.select(EInvoice).where(EInvoice.invoice_id == invoice.id))
    if existing: return jsonify({'item': existing.to_dict(), 'mode': 'api', 'existing': True})
    payload = request.get_json(silent=True) or {}; tax_mode = str(payload.get('tax_mode', 'CGST/SGST')).strip()
    if tax_mode not in {'CGST/SGST', 'IGST'}: return jsonify({'message': 'Tax mode must be CGST/SGST or IGST.'}), 400
    hsn_summary = payload.get('hsn_summary') if isinstance(payload.get('hsn_summary'), list) else []
    if not hsn_summary: hsn_summary = [{'hsn': '9403', 'description': 'Furniture and interiors', 'taxable_value': float(invoice.subtotal or 0)}]
    tax_total = Decimal(str(invoice.tax_amount or 0)); half = tax_total / 2
    customer_gstin = str(payload.get('gstin') or (invoice.customer.gstin if invoice.customer else '')).strip()
    item = EInvoice(invoice_id=invoice.id, gstin=customer_gstin, place_of_supply=str(payload.get('place_of_supply', '')).strip(), tax_mode=tax_mode, hsn_summary_json=json.dumps(hsn_summary), cgst_amount=half if tax_mode == 'CGST/SGST' else 0, sgst_amount=half if tax_mode == 'CGST/SGST' else 0, igst_amount=tax_total if tax_mode == 'IGST' else 0, irn=f'DEMO-{invoice.invoice_number}-{uuid4().hex[:16].upper()}', acknowledgement_number=f'ACK-{uuid4().hex[:10].upper()}', status='Generated')
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'E-invoice generated', 'e_invoice', item.id, item.irn); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@gst_bp.post('/<int:e_invoice_id>/eway-bill')
@roles_required('admin', 'sales')
def generate_eway_bill(e_invoice_id):
    item = db.get_or_404(EInvoice, e_invoice_id)
    if not item.eway_bill_number: item.eway_bill_number = f'EWB-{uuid4().hex[:12].upper()}'; item.status = 'E-way bill generated'; db.session.commit(); record_audit(current_user().id, 'E-way bill generated', 'e_invoice', item.id, item.eway_bill_number); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
