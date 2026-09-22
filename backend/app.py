from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from .config import Config
from .extensions import db, jwt, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(
        app,
        resources={r'/api/*': {'origins': app.config['FRONTEND_ORIGINS']}},
        supports_credentials=False,
    )

    from .routes.auth import auth_bp
    from .routes.products import products_bp
    from .routes.quotes import quotes_bp
    from .routes.customers import customers_bp
    from .routes.leads import leads_bp
    from .routes.uploads import uploads_bp
    from .routes.orders import orders_bp
    from .routes.inventory import inventory_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(quotes_bp, url_prefix='/api/quotes')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')

    if app.config.get('AUTO_SEED'):
        with app.app_context():
            from .seed import seed_database
            seed_database()

    @app.get('/api/health')
    def health():
        return jsonify({'ok': True, 'service': 'furnivo-api'})

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
