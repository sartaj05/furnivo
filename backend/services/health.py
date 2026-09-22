import os
from sqlalchemy import text
from ..extensions import db


def run_health_check(config):
    checks = {'database': 'ok', 'storage': 'cloudinary' if config.get('CLOUDINARY_URL') else 'local'}
    try:
        db.session.execute(text('SELECT 1'))
    except Exception:
        checks['database'] = 'error'
    status = 'ok' if checks['database'] == 'ok' else 'degraded'
    return {
        'status': status,
        'checks': checks,
        'service': 'furnivo-api',
        'version': config['APP_VERSION'],
        'environment': config['ENVIRONMENT'],
        'storage_provider': checks['storage'],
        'payment_provider': os.getenv('PAYMENT_PROVIDER', 'demo'),
    }
