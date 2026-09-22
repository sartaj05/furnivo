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


class QuoteClientAccess(TimestampMixin, db.Model):
    __tablename__ = 'quote_client_access'
    __table_args__ = (db.UniqueConstraint('quote_id', 'user_id', name='uq_quote_client_access'),)

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    last_action = db.Column(db.String(40), nullable=False, default='Pending')
    response_comment = db.Column(db.Text, nullable=False, default='')
    responded_at = db.Column(db.DateTime(timezone=True))
    quote = db.relationship('Quote')
    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'user_id': self.user_id,
            'last_action': self.last_action,
            'response_comment': self.response_comment,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
        }


class QuoteRevision(TimestampMixin, db.Model):
    __tablename__ = 'quote_revisions'

    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    comment = db.Column(db.Text, nullable=False, default='')
    changed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    quote = db.relationship('Quote')
    changed_by = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'version': self.version,
            'action': self.action,
            'status': self.status,
            'subtotal': float(self.subtotal or 0),
            'amount': float(self.amount or 0),
            'comment': self.comment,
            'changed_by': self.changed_by.public_dict() if self.changed_by else None,
            'created_at': self.created_at.isoformat(),
        }


class Order(TimestampMixin, db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False, unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    customer_name = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Confirmed')
    production_status = db.Column(db.String(40), nullable=False, default='Not started')
    delivery_date = db.Column(db.Date)
    installation_status = db.Column(db.String(40), nullable=False, default='Not scheduled')
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quote = db.relationship('Quote')
    customer = db.relationship('Customer')
    updates = db.relationship('ProjectUpdate', back_populates='order', cascade='all, delete-orphan', lazy='selectin')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'quote_id': self.quote_id,
            'quote_number': self.quote.quote_number if self.quote else None,
            'customer_id': self.customer_id,
            'customer': self.customer_name,
            'status': self.status,
            'production_status': self.production_status,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'installation_status': self.installation_status,
            'notes': self.notes,
            'amount': float(self.quote.total) if self.quote else 0,
            'updates': [update.to_dict() for update in sorted(self.updates, key=lambda item: item.created_at, reverse=True)],
        }


class ProjectUpdate(TimestampMixin, db.Model):
    __tablename__ = 'project_updates'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order', back_populates='updates')
    author = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'body': self.body, 'author': self.author.name if self.author else 'Team', 'created_at': self.created_at.isoformat()}


class InventoryItem(TimestampMixin, db.Model):
    __tablename__ = 'inventory_items'
    __table_args__ = (db.UniqueConstraint('product_id', 'variant_id', name='uq_inventory_product_variant'),)

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=True, index=True)
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reserved_quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reorder_level = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    supplier = db.Column(db.String(180), nullable=False, default='')
    location = db.Column(db.String(180), nullable=False, default='')
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')

    @property
    def available_quantity(self):
        return max((self.quantity or 0) - (self.reserved_quantity or 0), 0)

    @property
    def is_low_stock(self):
        return self.available_quantity <= (self.reorder_level or 0)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'product': self.product.name if self.product else None,
            'sku': self.variant.sku if self.variant else self.product.sku if self.product else None,
            'variant': self.variant.finish if self.variant else None,
            'quantity': float(self.quantity or 0),
            'reserved_quantity': float(self.reserved_quantity or 0),
            'available_quantity': float(self.available_quantity),
            'reorder_level': float(self.reorder_level or 0),
            'is_low_stock': self.is_low_stock,
            'supplier': self.supplier,
            'location': self.location,
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

class Lead(TimestampMixin, db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(180), nullable=False, default='')
    email = db.Column(db.String(255), nullable=False, default='')
    phone = db.Column(db.String(60), nullable=False, default='')
    source = db.Column(db.String(80), nullable=False, default='Website')
    stage = db.Column(db.String(40), nullable=False, default='New', index=True)
    value = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    owner = db.relationship('User')
    notes = db.relationship('LeadNote', back_populates='lead', cascade='all, delete-orphan', lazy='selectin')
    tasks = db.relationship('LeadTask', back_populates='lead', cascade='all, delete-orphan', lazy='selectin')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'company': self.company, 'email': self.email,
            'phone': self.phone, 'source': self.source, 'stage': self.stage, 'value': float(self.value or 0),
            'owner_id': self.owner_id, 'owner': self.owner.public_dict() if self.owner else None,
            'notes': [note.to_dict() for note in sorted(self.notes, key=lambda x: x.created_at, reverse=True)],
            'tasks': [task.to_dict() for task in sorted(self.tasks, key=lambda x: (x.is_done, x.due_date or __import__('datetime').date.max))],
        }


class LeadNote(TimestampMixin, db.Model):
    __tablename__ = 'lead_notes'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    lead = db.relationship('Lead', back_populates='notes')
    author = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'body': self.body, 'author': self.author.name if self.author else 'Team', 'created_at': self.created_at.isoformat()}


class LeadTask(TimestampMixin, db.Model):
    __tablename__ = 'lead_tasks'

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lead = db.relationship('Lead', back_populates='tasks')
    assigned_to = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_done': self.is_done, 'assigned_to_id': self.assigned_to_id,
            'assigned_to': self.assigned_to.name if self.assigned_to else None,
        }
