from werkzeug.security import generate_password_hash
from .extensions import db
from .models import Product, User


DEMO_PRODUCTS = [
    {"sku": "FUR-SOF-101", "name": "Aster Modular Sofa", "category": "Furniture", "price": 78500, "unit": "set", "material": "Oak frame, performance fabric", "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=80"},
    {"sku": "INT-LGT-204", "name": "Halo Pendant Light", "category": "Interiors", "price": 12400, "unit": "piece", "material": "Powder-coated metal, frosted glass", "image": "https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=900&q=80"},
    {"sku": "BLD-PNL-310", "name": "Terra Fluted Wall Panel", "category": "Building Material", "price": 920, "unit": "sq.ft", "material": "WPC acoustic panel", "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80"},
]

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

    for data in DEMO_PRODUCTS:
        if db.session.scalar(db.select(Product).where(Product.sku == data["sku"])):
            continue
        db.session.add(Product(**data))
    db.session.commit()
