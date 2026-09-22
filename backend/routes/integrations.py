from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import IntegrationConnection, SyncRun
from ..services.audit import record_audit
from ..utils import current_user, roles_required

integrations_bp = Blueprint('integrations', __name__)
PROVIDERS = {'Tally', 'Zoho Books', 'QuickBooks'}


@integrations_bp.get('')
@roles_required('admin')
def list_integrations():
    connections = db.session.scalars(db.select(IntegrationConnection).order_by(IntegrationConnection.id)).all()
    runs = db.session.scalars(db.select(SyncRun).order_by(SyncRun.id.desc()).limit(50)).all()
    return jsonify({'connections': [item.to_dict() for item in connections], 'runs': [item.to_dict() for item in runs], 'mode': 'api'})


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
    run = SyncRun(connection_id=item.id, entity=str((request.get_json(silent=True) or {}).get('entity', 'invoices')), status='Complete', records_synced=0, completed_at=datetime.now(timezone.utc))
    item.last_sync_at = run.completed_at; item.status = 'Synced'; db.session.add(run); db.session.commit()
    record_audit(current_user().id, 'Accounting sync completed', 'integration', item.id, f'{run.entity} sync completed in demo adapter'); db.session.commit()
    return jsonify({'item': run.to_dict(), 'connection': item.to_dict(), 'mode': 'api'})
