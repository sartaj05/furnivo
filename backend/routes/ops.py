import os
from flask import Blueprint, current_app, jsonify
from ..extensions import db
from ..services.ops import backup_database, list_backups, restore_backup, verify_backup
from ..services.health import run_health_check
from ..services.deployment import deployment_checks
from ..utils import roles_required

ops_bp = Blueprint('ops', __name__)


@ops_bp.get('/health')
@roles_required('admin')
def detailed_health():
    result = run_health_check(current_app.config)
    result.update({'database': result['checks']['database'], 'auto_seed': current_app.config['AUTO_SEED'], 'rate_limit_per_minute': current_app.config['RATE_LIMIT_PER_MINUTE'], 'mode': 'api'})
    return jsonify(result), 200 if result['status'] == 'ok' else 503


@ops_bp.get('/deployment-checks')
@roles_required('admin')
def deployment_readiness():
    return jsonify(deployment_checks(current_app.config))


@ops_bp.get('/backups')
@roles_required('admin')
def backups(): return jsonify({'items': list_backups(current_app), 'mode': 'api'})


@ops_bp.post('/backups')
@roles_required('admin')
def create_backup():
    try: return jsonify({'item': backup_database(current_app), 'mode': 'api'}), 201
    except RuntimeError as exc: return jsonify({'message': str(exc)}), 503


@ops_bp.get('/backups/<path:filename>/verify')
@roles_required('admin')
def verify_backup_file(filename):
    item = verify_backup(current_app, filename)
    if not item: return jsonify({'message': 'Backup file not found.'}), 404
    return jsonify({'item': item, 'mode': 'api'})


@ops_bp.post('/backups/<path:filename>/restore')
@roles_required('admin')
def restore_backup_file(filename):
    try: return jsonify({'item': restore_backup(current_app, filename), 'mode': 'api'}), 200
    except FileNotFoundError as exc: return jsonify({'message': str(exc)}), 404
    except RuntimeError as exc: return jsonify({'message': str(exc)}), 501
