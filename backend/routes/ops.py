import os
from flask import Blueprint, current_app, jsonify
from ..extensions import db
from ..services.ops import backup_database, list_backups
from ..services.health import run_health_check
from ..utils import roles_required

ops_bp = Blueprint('ops', __name__)


@ops_bp.get('/health')
@roles_required('admin')
def detailed_health():
    result = run_health_check(current_app.config)
    result.update({'database': result['checks']['database'], 'auto_seed': current_app.config['AUTO_SEED'], 'rate_limit_per_minute': current_app.config['RATE_LIMIT_PER_MINUTE'], 'mode': 'api'})
    return jsonify(result), 200 if result['status'] == 'ok' else 503


@ops_bp.get('/backups')
@roles_required('admin')
def backups(): return jsonify({'items': list_backups(current_app), 'mode': 'api'})


@ops_bp.post('/backups')
@roles_required('admin')
def create_backup():
    try: return jsonify({'item': backup_database(current_app), 'mode': 'api'}), 201
    except RuntimeError as exc: return jsonify({'message': str(exc)}), 503
