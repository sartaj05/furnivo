import os
from flask import Blueprint, current_app, jsonify
from ..extensions import db
from ..services.ops import backup_database, list_backups
from ..utils import roles_required

ops_bp = Blueprint('ops', __name__)


@ops_bp.get('/health')
@roles_required('admin')
def detailed_health():
    database = 'ok'
    try: db.session.execute(db.text('SELECT 1'))
    except Exception: database = 'error'
    return jsonify({'status': 'ok' if database == 'ok' else 'degraded', 'version': current_app.config['APP_VERSION'], 'environment': current_app.config['ENVIRONMENT'], 'database': database, 'payment_provider': os.getenv('PAYMENT_PROVIDER', 'demo'), 'auto_seed': current_app.config['AUTO_SEED'], 'rate_limit_per_minute': current_app.config['RATE_LIMIT_PER_MINUTE'], 'mode': 'api'}), 200 if database == 'ok' else 503


@ops_bp.get('/backups')
@roles_required('admin')
def backups(): return jsonify({'items': list_backups(current_app), 'mode': 'api'})


@ops_bp.post('/backups')
@roles_required('admin')
def create_backup():
    try: return jsonify({'item': backup_database(current_app), 'mode': 'api'}), 201
    except RuntimeError as exc: return jsonify({'message': str(exc)}), 503
