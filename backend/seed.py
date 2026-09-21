from werkzeug.security import generate_password_hash
from .extensions import db
from .models import Product, ProductVariant, Quote, QuoteItem, User


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

    sofa = db.session.scalar(db.select(Product).where(Product.sku == "FUR-SOF-101"))
    if sofa and not sofa.variants:
        sofa.variants.extend([
            ProductVariant(sku="FUR-SOF-101-SAND", finish="Sand Boucle", width_mm=2600, height_mm=780, depth_mm=980, price_delta=0),
            ProductVariant(sku="FUR-SOF-101-OLIVE", finish="Olive Performance", width_mm=2600, height_mm=780, depth_mm=980, price_delta=4500),
        ])
        db.session.commit()


def seed_quotes():
    if db.session.scalar(db.select(Quote).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.role == "admin"))
    sofa = db.session.scalar(db.select(Product).where(Product.sku == "FUR-SOF-101"))
    light = db.session.scalar(db.select(Product).where(Product.sku == "INT-LGT-204"))
    if not admin or not sofa:
        return
    quote = Quote(quote_number="Q-1042", customer_name="Northline Studio", status="Sent", quote_date=__import__('datetime').date(2026, 9, 18), created_by_id=admin.id)
    quote.items = [QuoteItem(product_id=sofa.id, description=sofa.name, sku=sofa.sku, quantity=2, unit=sofa.unit, unit_price=sofa.price)]
    if light:
        quote.items.append(QuoteItem(product_id=light.id, description=light.name, sku=light.sku, quantity=2, unit=light.unit, unit_price=light.price))
    db.session.add(quote)
    db.session.commit()
