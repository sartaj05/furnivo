from datetime import datetime, timezone
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class User(TimestampMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='client', index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def public_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
        }

class Product(TimestampMixin, db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    unit = db.Column(db.String(40), nullable=False, default='piece')
    material = db.Column(db.String(255), nullable=False, default='')
    description = db.Column(db.Text, nullable=False, default='')
    image = db.Column(db.String(500), nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'category': self.category,
            'price': float(self.price or 0),
            'unit': self.unit,
            'material': self.material,
            'description': self.description,
            'image': self.image,
            'is_active': self.is_active,
        }
