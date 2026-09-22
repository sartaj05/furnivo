import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _database_uri():
    url = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'furnivo.db'}")
    # Normalize legacy Heroku-style PostgreSQL URLs.
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    APP_VERSION = os.getenv('APP_VERSION', 'furnivo-v3')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-change-me')
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')))
    REFRESH_TOKEN_DAYS = int(os.getenv('REFRESH_TOKEN_DAYS', '30'))
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = os.getenv('ENVIRONMENT', 'development') == 'production'
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(8 * 1024 * 1024)))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv('FRONTEND_ORIGINS', '*').split(',')
        if origin.strip()
    ]
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
    CLOUDINARY_FOLDER = os.getenv('CLOUDINARY_FOLDER', 'furnivo')
    AUTO_SEED = os.getenv('AUTO_SEED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '120'))
    BACKUP_FOLDER = os.getenv('BACKUP_FOLDER', str(BASE_DIR / 'backups'))
    EINVOICE_PROVIDER = os.getenv('EINVOICE_PROVIDER', 'demo')
