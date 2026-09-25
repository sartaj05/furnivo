import os


def deployment_checks(config):
    environment = str(config.get('ENVIRONMENT', 'development')).lower()
    production_like = environment in {'staging', 'production'}
    e2e_required = production_like and os.getenv('REQUIRE_E2E_CHECKS', 'true').lower() == 'true'
    secret = str(config.get('SECRET_KEY', ''))
    jwt_secret = str(config.get('JWT_SECRET_KEY', ''))
    database_url = str(config.get('SQLALCHEMY_DATABASE_URI', ''))
    checks = [
        {'name': 'Application secrets', 'ok': len(secret) >= 32 and len(jwt_secret) >= 32 and 'change-before-production' not in secret, 'detail': 'SECRET_KEY and JWT_SECRET_KEY must be long, private values.'},
        {'name': 'Seed policy', 'ok': not production_like or not config.get('AUTO_SEED', True), 'detail': 'AUTO_SEED should be false outside development.'},
        {'name': 'Database', 'ok': not production_like or not database_url.startswith('sqlite:'), 'detail': 'Use PostgreSQL or MySQL for staging and production.'},
        {'name': 'Frontend origins', 'ok': not production_like or '*' not in config.get('FRONTEND_ORIGINS', []), 'detail': 'Restrict CORS to the deployed frontend origin.'},
        {'name': 'Payment webhooks', 'ok': not production_like or bool(os.getenv('PAYMENT_WEBHOOK_SECRET') or os.getenv('STRIPE_WEBHOOK_SECRET') or os.getenv('RAZORPAY_WEBHOOK_SECRET')), 'detail': 'Configure a provider webhook secret before accepting live payments.'},
        {'name': 'Playwright smoke target', 'ok': not e2e_required or bool(os.getenv('E2E_BASE_URL')), 'detail': 'Set E2E_BASE_URL so the deployment pipeline can run browser smoke tests against the deployed frontend.'},
    ]
    return {'environment': environment, 'ready': all(item['ok'] for item in checks), 'checks': checks, 'mode': 'api'}
