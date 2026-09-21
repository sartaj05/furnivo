from werkzeug.security import generate_password_hash
from .extensions import db
from .models import User

DEMO_USERS = [
    ('Aarav Admin', 'admin@furnivo.demo', 'admin123', 'admin'),
    ('Meera Sales', 'sales@furnivo.demo', 'sales123', 'sales'),
    ('Kabir Designer', 'designer@furnivo.demo', 'design123', 'designer'),
    ('Riya Client', 'client@furnivo.demo', 'client123', 'client'),
]


def seed_database():
    db.create_all()
    for name, email, password, role in DEMO_USERS:
        existing = db.session.scalar(db.select(User).where(User.email == email))
        if existing:
            continue
        db.session.add(
            User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
        )
    db.session.commit()
