import json
import logging
import sys
import time
from pathlib import Path
from uuid import uuid4
from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import inspect, text
from werkzeug.exceptions import HTTPException

# Support both `python -m backend.app` from the project root and
# `python app.py` from inside the backend directory.
if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = 'backend'

from .config import Config
from .extensions import db, jwt, migrate
from .services.health import run_health_check


def prepare_development_schema(app):
    """Bring legacy local SQLite files up to the current migration head.

    Older local versions created tables with ``db.create_all()`` and therefore
    have no Alembic version row. We know those files contain the pre-tenant
    production schema, so stamp that revision and apply only the pending
    tenant/rework migration. Empty databases still run the full migration set.
    Production uses the explicit deployment migration command instead.
    """
    if not app.config.get('AUTO_SEED') or app.config.get('ENVIRONMENT') not in {'development', 'local'}:
        return
    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())
        from flask_migrate import stamp, upgrade
        if not tables:
            upgrade()
            return
        if 'alembic_version' not in tables:
            expected_legacy_tables = {'users', 'production_jobs', 'production_tasks', 'quality_inspections'}
            if not expected_legacy_tables.issubset(tables):
                raise RuntimeError('Legacy database schema detected. Back up the database and run `flask --app backend.app db upgrade` manually before starting the app.')
            stamp(revision='g6b9d5e23f71')
        upgrade()


def repair_legacy_sqlite_columns(app):
    """Add columns missing from very old local SQLite tables.

    ``create_all`` creates new tables but never alters existing ones. This
    keeps old demo databases usable after several feature migrations. It is
    intentionally limited to development SQLite and only adds columns from
    the current SQLAlchemy metadata; production remains migration-driven.
    """
    if not app.config.get('AUTO_SEED') or app.config.get('ENVIRONMENT') not in {'development', 'local'}:
        return
    if not str(app.config.get('SQLALCHEMY_DATABASE_URI', '')).startswith('sqlite:'):
        return
    engine = db.engine
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    quote = engine.dialect.identifier_preparer.quote

    def default_sql(column):
        type_name = column.type.__class__.__name__.lower()
        if 'date' in type_name or 'time' in type_name:
            return 'CURRENT_TIMESTAMP' if 'time' in type_name else 'CURRENT_DATE'
        if any(token in type_name for token in ('integer', 'numeric', 'decimal', 'float', 'real')):
            return '0'
        if 'boolean' in type_name:
            return '0'
        return "''"

    with engine.begin() as connection:
        for table in db.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {column['name'] for column in inspect(connection).get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns or column.primary_key:
                    continue
                sql = f'ALTER TABLE {quote(table.name)} ADD COLUMN {quote(column.name)} {column.type.compile(dialect=engine.dialect)}'
                if not column.nullable:
                    sql += f' NOT NULL DEFAULT {default_sql(column)}'
                connection.execute(text(sql))


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db, directory=str(Path(app.root_path).parent / 'migrations'))
    CORS(
        app,
        resources={r'/api/*': {'origins': app.config['FRONTEND_ORIGINS']}},
        supports_credentials=False,
    )

    rate_buckets = {}

    @app.before_request
    def operational_request_start():
        g.request_id = request.headers.get('X-Request-ID') or uuid4().hex
        if not request.path.startswith('/api/') or app.config['RATE_LIMIT_PER_MINUTE'] <= 0:
            return None
        now = time.monotonic(); client = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
        started, count = rate_buckets.get(client, (now, 0))
        if now - started >= 60: started, count = now, 0
        count += 1; rate_buckets[client] = (started, count)
        if count > app.config['RATE_LIMIT_PER_MINUTE']:
            response = jsonify({'message': 'Rate limit exceeded. Try again shortly.', 'request_id': g.request_id})
            response.status_code = 429; response.headers['Retry-After'] = '60'; return response
        return None

    @app.after_request
    def operational_request_end(response):
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        app.logger.info(json.dumps({'event': 'request_complete', 'request_id': getattr(g, 'request_id', ''), 'method': request.method, 'path': request.path, 'status': response.status_code, 'remote': request.remote_addr}))
        return response

    @app.errorhandler(Exception)
    def api_error(error):
        if isinstance(error, HTTPException):
            if request.path.startswith('/api/'):
                return jsonify({'message': error.description, 'request_id': getattr(g, 'request_id', '')}), error.code
            return error
        app.logger.exception('Unhandled application error', exc_info=error)
        if request.path.startswith('/api/'):
            return jsonify({'message': 'Unexpected server error.', 'request_id': getattr(g, 'request_id', '')}), 500
        raise error

    from .routes.auth import auth_bp
    from .routes.products import products_bp
    from .routes.quotes import quotes_bp
    from .routes.customers import customers_bp
    from .routes.leads import leads_bp
    from .routes.uploads import uploads_bp
    from .routes.orders import orders_bp
    from .routes.inventory import inventory_bp
    from .routes.notifications import notifications_bp
    from .routes.invoices import invoices_bp
    from .routes.procurement import procurement_bp
    from .routes.reports import reports_bp
    from .routes.audit import audit_bp
    from .routes.payments import payments_bp
    from .routes.scheduling import scheduling_bp
    from .routes.warehouses import warehouses_bp
    from .routes.returns import returns_bp
    from .routes.configurator import configurator_bp
    from .routes.production import production_bp
    from .routes.reconciliation import reconciliation_bp
    from .routes.contracts import contracts_bp
    from .routes.portal import portal_bp
    from .routes.ops import ops_bp
    from .routes.gst import gst_bp
    from .routes.data_admin import data_admin_bp
    from .routes.access import access_bp
    from .routes.service import service_bp
    from .routes.analytics import analytics_bp
    from .routes.integrations import integrations_bp
    from .routes.field import field_bp
    from .routes.business import business_bp
    from .routes.branches import branches_bp
    from .routes.recommendations import recommendations_bp
    from .routes.design_assistant import design_bp
    from .routes.tenants import tenants_bp
    from .routes.dashboard import dashboard_bp
    from .routes.live import live_bp
    from .routes.predictive import predictive_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(quotes_bp, url_prefix='/api/quotes')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(invoices_bp, url_prefix='/api/invoices')
    app.register_blueprint(procurement_bp, url_prefix='/api/procurement')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(audit_bp, url_prefix='/api/audit-logs')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(scheduling_bp, url_prefix='/api/schedules')
    app.register_blueprint(warehouses_bp, url_prefix='/api/warehouses')
    app.register_blueprint(returns_bp, url_prefix='/api/returns')
    app.register_blueprint(configurator_bp, url_prefix='/api/quote-config')
    app.register_blueprint(production_bp, url_prefix='/api/production')
    app.register_blueprint(reconciliation_bp, url_prefix='/api/payment-reconciliation')
    app.register_blueprint(contracts_bp, url_prefix='/api/contracts')
    app.register_blueprint(portal_bp, url_prefix='/api/portal')
    app.register_blueprint(ops_bp, url_prefix='/api/ops')
    app.register_blueprint(gst_bp, url_prefix='/api/gst')
    app.register_blueprint(data_admin_bp, url_prefix='/api/data-admin')
    app.register_blueprint(access_bp, url_prefix='/api/access')
    app.register_blueprint(service_bp, url_prefix='/api/service')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(integrations_bp, url_prefix='/api/integrations')
    app.register_blueprint(field_bp, url_prefix='/api/field')
    app.register_blueprint(business_bp, url_prefix='/api/business')
    app.register_blueprint(branches_bp, url_prefix='/api/branches')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    app.register_blueprint(design_bp, url_prefix='/api/design-assistant')
    app.register_blueprint(tenants_bp, url_prefix='/api/tenants')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(live_bp, url_prefix='/api/live')
    app.register_blueprint(predictive_bp, url_prefix='/api/analytics/predictive')

    if app.config.get('AUTO_SEED'):
        with app.app_context():
            prepare_development_schema(app)
            repair_legacy_sqlite_columns(app)
            from .seed import seed_database
            seed_database()

    @app.get('/api/health')
    def health():
        result = run_health_check(app.config)
        return jsonify({'ok': result['status'] == 'ok', **result}), 200 if result['status'] == 'ok' else 503

    @app.get('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.cli.command('seed')
    def seed_command():
        from .seed import seed_database
        seed_database()
        print('Furnivo demo data seeded.')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
