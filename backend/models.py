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
    variants = db.relationship('ProductVariant', back_populates='product', cascade='all, delete-orphan', lazy='selectin')

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
            'variants': [variant.to_dict() for variant in self.variants],
        }


class ProductVariant(TimestampMixin, db.Model):
    __tablename__ = 'product_variants'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    finish = db.Column(db.String(120), nullable=False, default='Standard')
    width_mm = db.Column(db.Integer)
    height_mm = db.Column(db.Integer)
    depth_mm = db.Column(db.Integer)
    price_delta = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    stock_status = db.Column(db.String(40), nullable=False, default='Made to order')
    product = db.relationship('Product', back_populates='variants')

    def to_dict(self):
        dimensions = ' × '.join(str(v) for v in [self.width_mm, self.height_mm, self.depth_mm] if v)
        return {
            'id': self.id, 'product_id': self.product_id, 'sku': self.sku, 'finish': self.finish,
            'width_mm': self.width_mm, 'height_mm': self.height_mm, 'depth_mm': self.depth_mm,
            'dimensions': f'{dimensions} mm' if dimensions else '',
            'price_delta': float(self.price_delta or 0), 'stock_status': self.stock_status,
        }

class Quote(TimestampMixin, db.Model):
    __tablename__ = 'quotes'

    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(180), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    customer = db.relationship('Customer')
    status = db.Column(db.String(40), nullable=False, default='Draft', index=True)
    quote_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=False, default='')
    discount_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    tax_percent = db.Column(db.Numeric(6, 2), nullable=False, default=18)
    shipping_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.relationship('QuoteItem', back_populates='quote', cascade='all, delete-orphan', lazy='selectin')

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items), 0)

    @property
    def discount_amount(self):
        return self.subtotal * (self.discount_percent or 0) / 100

    @property
    def taxable_amount(self):
        return max(self.subtotal - self.discount_amount, 0)

    @property
    def tax_amount(self):
        return self.taxable_amount * (self.tax_percent or 0) / 100

    @property
    def total(self):
        return self.taxable_amount + self.tax_amount + (self.shipping_amount or 0)

    def to_dict(self):
        return {
            'id': self.quote_number,
            'database_id': self.id,
            'customer': self.customer_name,
            'customer_id': self.customer_id,
            'customer_record': self.customer.to_dict() if self.customer else None,
            'status': self.status,
            'date': self.quote_date.isoformat(),
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'subtotal': float(self.subtotal),
            'discount_percent': float(self.discount_percent or 0),
            'discount_amount': float(self.discount_amount),
            'tax_percent': float(self.tax_percent or 0),
            'tax_amount': float(self.tax_amount),
            'shipping_amount': float(self.shipping_amount or 0),
            'amount': float(self.total),
        }


class QuoteItem(TimestampMixin, db.Model):
    __tablename__ = 'quote_items'

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), nullable=False, default='')
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    unit = db.Column(db.String(40), nullable=False, default='piece')
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    quote = db.relationship('Quote', back_populates='items')
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')

    @property
    def line_total(self):
        return (self.quantity or 0) * (self.unit_price or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'description': self.description,
            'sku': self.sku,
            'quantity': float(self.quantity or 0),
            'unit': self.unit,
            'unit_price': float(self.unit_price or 0),
            'line_total': float(self.line_total),
        }

class Customer(TimestampMixin, db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(180), nullable=False, index=True)
    contact_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), nullable=False, default='')
    phone = db.Column(db.String(60), nullable=False, default='')
    billing_address = db.Column(db.Text, nullable=False, default='')
    project_address = db.Column(db.Text, nullable=False, default='')
    gstin = db.Column(db.String(40), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            'id': self.id, 'company': self.company, 'contact_name': self.contact_name,
            'email': self.email, 'phone': self.phone, 'billing_address': self.billing_address,
            'project_address': self.project_address, 'gstin': self.gstin, 'notes': self.notes,
            'is_active': self.is_active,
        }
