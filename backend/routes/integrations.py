from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import EInvoice, IntegrationConnection, Invoice, SyncRun
from ..services.audit import record_audit
from ..utils import current_user, roles_required

integrations_bp = Blueprint('integrations', __name__)
PROVIDERS = {'Tally', 'Zoho Books', 'QuickBooks'}
EXPORT_ENTITIES = {'invoices', 'e_invoices', 'payments'}


def _accounting_status(connection=None):
    connections = [connection] if connection else db.session.scalars(db.select(IntegrationConnection).order_by(IntegrationConnection.id)).all()
    return {
        'providers': sorted(PROVIDERS),
        'connections': [{
            'id': item.id,
            'provider': item.provider,
            'status': item.status,
            'enabled': item.is_enabled,
            'credentials_configured': bool(item.credentials_ref),
            'last_sync_at': item.last_sync_at.isoformat() if item.last_sync_at else None,
        } for item in connections],
        'environment': 'configured' if any(item.credentials_ref for item in connections) else 'demo',
        'webhook_note': 'Outbound provider sync is adapter-ready; configure provider credentials before live export.',
    }


def _export_records(entity):
    if entity == 'invoices':
        invoices = db.session.scalars(db.select(Invoice).order_by(Invoice.id)).all()
        return [{
            'invoice_number': item.invoice_number,
            'customer': item.customer_name,
            'issue_date': item.issue_date.isoformat(),
            'due_date': item.due_date.isoformat() if item.due_date else None,
            'subtotal': float(item.subtotal or 0),
            'tax_amount': float(item.tax_amount or 0),
            'total': float(item.total or 0),
            'amount_paid': float(item.amount_paid or 0),
            'accounting_status': item.accounting_status,
        } for item in invoices]
    if entity == 'e_invoices':
        return [{
            'invoice_number': item.invoice.invoice_number if item.invoice else None,
            'gstin': item.gstin,
            'place_of_supply': item.place_of_supply,
            'tax_mode': item.tax_mode,
            'irn': item.irn,
            'status': item.status,
            'cgst_amount': float(item.cgst_amount or 0),
            'sgst_amount': float(item.sgst_amount or 0),
            'igst_amount': float(item.igst_amount or 0),
        } for item in db.session.scalars(db.select(EInvoice).order_by(EInvoice.id)).all()]
    invoices = db.session.scalars(db.select(Invoice).order_by(Invoice.id)).all()
    return [{
        'invoice_number': invoice.invoice_number,
        'payment_id': payment.id,
        'amount': float(payment.amount or 0),
        'method': payment.method,
        'reference': payment.reference,
        'paid_at': payment.paid_at.isoformat(),
    } for invoice in invoices for payment in invoice.payments]


@integrations_bp.get('')
@roles_required('admin')
def list_integrations():
    connections = db.session.scalars(db.select(IntegrationConnection).order_by(IntegrationConnection.id)).all()
    runs = db.session.scalars(db.select(SyncRun).order_by(SyncRun.id.desc()).limit(50)).all()
    return jsonify({'connections': [item.to_dict() for item in connections], 'runs': [item.to_dict() for item in runs], 'status': _accounting_status(), 'mode': 'api'})


@integrations_bp.get('/accounting-status')
@roles_required('admin')
def accounting_status():
    return jsonify({'status': _accounting_status(), 'mode': 'api'})


@integrations_bp.post('')
@roles_required('admin')
def create_integration():
    payload = request.get_json(silent=True) or {}; provider = str(payload.get('provider', '')).strip()
    if provider not in PROVIDERS:
        return jsonify({'message': f'Provider must be one of: {", ".join(sorted(PROVIDERS))}.'}), 400
    credentials = str(payload.get('credentials_ref', '')).strip()
    if not credentials:
        return jsonify({'message': 'Use a secret reference, never a raw API key.'}), 400
    item = IntegrationConnection(name=str(payload.get('name', provider)).strip() or provider, provider=provider, base_url=str(payload.get('base_url', '')).strip(), external_account=str(payload.get('external_account', '')).strip(), credentials_ref=credentials, status='Connected')
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Accounting integration created', 'integration', item.id, f'{provider} connection'); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@integrations_bp.patch('/<int:connection_id>')
@roles_required('admin')
def update_integration(connection_id):
    item = db.get_or_404(IntegrationConnection, connection_id); payload = request.get_json(silent=True) or {}
    if 'is_enabled' in payload: item.is_enabled = bool(payload['is_enabled'])
    if 'name' in payload: item.name = str(payload['name']).strip() or item.name
    db.session.commit(); record_audit(current_user().id, 'Accounting integration updated', 'integration', item.id, item.status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@integrations_bp.post('/<int:connection_id>/sync')
@roles_required('admin')
def sync_integration(connection_id):
    item = db.get_or_404(IntegrationConnection, connection_id)
    if not item.is_enabled:
        return jsonify({'message': 'Enable the connection before syncing.'}), 400
    entity = str((request.get_json(silent=True) or {}).get('entity', 'invoices'))
    if entity not in EXPORT_ENTITIES:
        return jsonify({'message': f'Entity must be one of: {", ".join(sorted(EXPORT_ENTITIES))}.'}), 400
    run = SyncRun(connection_id=item.id, entity=entity, status='Complete', records_synced=len(_export_records(entity)), completed_at=datetime.now(timezone.utc))
    item.last_sync_at = run.completed_at; item.status = 'Synced'; db.session.add(run); db.session.commit()
    record_audit(current_user().id, 'Accounting sync completed', 'integration', item.id, f'{run.entity} sync completed in demo adapter'); db.session.commit()
    return jsonify({'item': run.to_dict(), 'connection': item.to_dict(), 'mode': 'api'})


@integrations_bp.post('/<int:connection_id>/export')
@roles_required('admin')
def export_integration(connection_id):
    item = db.get_or_404(IntegrationConnection, connection_id)
    if not item.is_enabled:
        return jsonify({'message': 'Enable the connection before exporting.'}), 400
    payload = request.get_json(silent=True) or {}
    entity = str(payload.get('entity', 'invoices'))
    if entity not in EXPORT_ENTITIES:
        return jsonify({'message': f'Entity must be one of: {", ".join(sorted(EXPORT_ENTITIES))}.'}), 400
    records = _export_records(entity)
    record = {'provider': item.provider, 'external_account': item.external_account, 'entity': entity, 'record_count': len(records), 'records': records, 'delivery': 'adapter-ready', 'message': 'Preview generated. Configure the provider adapter for live delivery.'}
    record_audit(current_user().id, 'Accounting export prepared', 'integration', item.id, f'{entity}: {len(records)} records')
    db.session.commit()
    return jsonify({'export': record, 'mode': 'api'})
