import pytest
from pathlib import Path
from backend.app import create_app

TEST_ROOT = Path(__file__).resolve().parent


class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key-for-tests-only'
    JWT_SECRET_KEY = 'test-jwt-secret-key-for-tests-only'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_ORIGINS = ['*']
    AUTO_SEED = True
    RATE_LIMIT_PER_MINUTE = 1000
    APP_VERSION = 'test'
    ENVIRONMENT = 'test'
    REFRESH_TOKEN_DAYS = 30
    JWT_ACCESS_TOKEN_EXPIRES = __import__('datetime').timedelta(hours=1)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    BACKUP_FOLDER = str(TEST_ROOT / '.backups')
    UPLOAD_FOLDER = str(TEST_ROOT / '.uploads')


@pytest.fixture()
def app():
    return create_app(TestConfig)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_headers(client):
    response = client.post('/api/auth/login', json={'email': 'admin@furnivo.demo', 'password': 'admin123'})
    return {'Authorization': f"Bearer {response.json['token']}"}
