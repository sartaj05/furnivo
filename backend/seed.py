from .extensions import db


def seed_database():
    db.create_all()
