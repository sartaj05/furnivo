import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _database_uri():
    url = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'furnivo.db'}")
    # Heroku-style postgres URLs still appear in the wild because apparently URLs needed legacy drama.
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-change-me')
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(8 * 1024 * 1024)))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv('FRONTEND_ORIGINS', '*').split(',')
        if origin.strip()
    ]
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
    AUTO_SEED = os.getenv('AUTO_SEED', 'true').lower() == 'true'
