import json
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
    active_tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True)
    active_tenant = db.relationship('Tenant', foreign_keys=[active_tenant_id])

    def public_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active_tenant_id': self.active_tenant_id,
        }


class RefreshSession(TimestampMixin, db.Model):
    __tablename__ = 'refresh_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True))
    user_agent = db.Column(db.String(255), nullable=False, default='')
    ip_address = db.Column(db.String(80), nullable=False, default='')
    user = db.relationship('User')

    def to_dict(self): return {'id': self.id, 'created_at': self.created_at.isoformat(), 'expires_at': self.expires_at.isoformat(), 'revoked': bool(self.revoked_at), 'user_agent': self.user_agent, 'ip_address': self.ip_address}


class MfaSetting(TimestampMixin, db.Model):
    __tablename__ = 'mfa_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    method = db.Column(db.String(40), nullable=False, default='demo-otp')
    user = db.relationship('User')


class MfaChallenge(TimestampMixin, db.Model):
    __tablename__ = 'mfa_challenges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    code_hash = db.Column(db.String(128), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True))
    user = db.relationship('User')

class Product(TimestampMixin, db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
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


class FurnitureConfiguration(TimestampMixin, db.Model):
    __tablename__ = 'furniture_configurations'

    id = db.Column(db.Integer, primary_key=True)
    configuration_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    name = db.Column(db.String(180), nullable=False)
    room = db.Column(db.String(120), nullable=False, default='')
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False, default='Saved')
    items_json = db.Column(db.Text, nullable=False, default='[]')
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    customer = db.relationship('Customer')
    quote = db.relationship('Quote', foreign_keys=[quote_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    @property
    def items(self):
        try:
            return json.loads(self.items_json or '[]')
        except (TypeError, ValueError):
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'configuration_number': self.configuration_number,
            'name': self.name,
            'room': self.room,
            'customer_id': self.customer_id,
            'customer': self.customer.company if self.customer else None,
            'quote_id': self.quote.quote_number if self.quote else None,
            'status': self.status,
            'items': self.items,
            'subtotal': float(self.subtotal or 0),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
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


class Notification(TimestampMixin, db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False, default='info')
    channel = db.Column(db.String(40), nullable=False, default='in_app')
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False, default='')
    related_type = db.Column(db.String(40), nullable=False, default='')
    related_id = db.Column(db.String(80), nullable=False, default='')
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    delivery_status = db.Column(db.String(30), nullable=False, default='delivered')
    scheduled_for = db.Column(db.DateTime(timezone=True))
    user = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'channel': self.channel,
            'title': self.title,
            'body': self.body,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'delivery_status': self.delivery_status,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'created_at': self.created_at.isoformat(),
        }


class NotificationDelivery(TimestampMixin, db.Model):
    __tablename__ = 'notification_deliveries'

    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id', ondelete='CASCADE'), nullable=False, index=True)
    channel = db.Column(db.String(40), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='queued')
    error = db.Column(db.Text, nullable=False, default='')
    attempted_at = db.Column(db.DateTime(timezone=True))
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    next_attempt_at = db.Column(db.DateTime(timezone=True))
    provider_message_id = db.Column(db.String(180), nullable=False, default='')
    notification = db.relationship('Notification')

    def to_dict(self):
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'channel': self.channel,
            'recipient': self.recipient,
            'status': self.status,
            'error': self.error,
            'attempt_count': self.attempt_count,
            'next_attempt_at': self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            'provider_message_id': self.provider_message_id,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
        }


class Invoice(TimestampMixin, db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    customer_name = db.Column(db.String(180), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(40), nullable=False, default='Sent')
    invoice_type = db.Column(db.String(30), nullable=False, default='Final')
    deposit_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_link = db.Column(db.String(500), nullable=False, default='')
    accounting_status = db.Column(db.String(40), nullable=False, default='Pending')
    reminder_sent_at = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')
    customer = db.relationship('Customer')
    payments = db.relationship('Payment', back_populates='invoice', cascade='all, delete-orphan', lazy='selectin')

    @property
    def balance(self):
        return max((self.total or 0) - (self.amount_paid or 0), 0)

    def refresh_status(self):
        if self.amount_paid >= self.total:
            self.status = 'Paid'
        elif self.amount_paid > 0:
            self.status = 'Partially Paid'
        elif self.due_date and self.due_date < __import__('datetime').date.today():
            self.status = 'Overdue'
        else:
            self.status = 'Sent'

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'customer_id': self.customer_id,
            'customer': self.customer_name,
            'issue_date': self.issue_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'invoice_type': self.invoice_type,
            'deposit_percent': float(self.deposit_percent or 0),
            'subtotal': float(self.subtotal or 0),
            'tax_amount': float(self.tax_amount or 0),
            'total': float(self.total or 0),
            'amount_paid': float(self.amount_paid or 0),
            'balance': float(self.balance),
            'payment_link': self.payment_link,
            'accounting_status': self.accounting_status,
            'reminder_sent_at': self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
            'notes': self.notes,
            'payments': [payment.to_dict() for payment in sorted(self.payments, key=lambda item: item.paid_at, reverse=True)],
        }


class Payment(TimestampMixin, db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(40), nullable=False, default='Bank transfer')
    reference = db.Column(db.String(120), nullable=False, default='')
    paid_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    invoice = db.relationship('Invoice', back_populates='payments')

    def to_dict(self):
        return {'id': self.id, 'amount': float(self.amount or 0), 'method': self.method, 'reference': self.reference, 'paid_at': self.paid_at.isoformat()}


class Supplier(TimestampMixin, db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, default='')
    phone = db.Column(db.String(60), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'phone': self.phone, 'notes': self.notes, 'is_active': self.is_active}


class PurchaseOrder(TimestampMixin, db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default='Draft')
    order_date = db.Column(db.Date, nullable=False)
    expected_date = db.Column(db.Date)
    supplier_quote_ref = db.Column(db.String(120), nullable=False, default='')
    actual_delivery_date = db.Column(db.Date)
    landed_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    quality_rating = db.Column(db.Numeric(3, 1), nullable=False, default=0)
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier = db.relationship('Supplier')
    items = db.relationship('PurchaseOrderItem', back_populates='purchase_order', cascade='all, delete-orphan', lazy='selectin')

    @property
    def total(self):
        return sum((item.line_total for item in self.items), 0)

    def to_dict(self):
        return {'id': self.id, 'po_number': self.po_number, 'supplier_id': self.supplier_id, 'supplier': self.supplier.name if self.supplier else None, 'status': self.status, 'order_date': self.order_date.isoformat(), 'expected_date': self.expected_date.isoformat() if self.expected_date else None, 'supplier_quote_ref': self.supplier_quote_ref, 'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None, 'landed_cost': float(self.landed_cost or 0), 'quality_rating': float(self.quality_rating or 0), 'notes': self.notes, 'total': float(self.total), 'items': [item.to_dict() for item in self.items]}


class PurchaseOrderItem(TimestampMixin, db.Model):
    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    purchase_order = db.relationship('PurchaseOrder', back_populates='items')
    product = db.relationship('Product')

    @property
    def line_total(self): return (self.quantity or 0) * (self.unit_cost or 0)

    def to_dict(self): return {'id': self.id, 'product_id': self.product_id, 'description': self.description, 'quantity': float(self.quantity or 0), 'unit_cost': float(self.unit_cost or 0), 'line_total': float(self.line_total)}


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(60), nullable=False)
    resource_id = db.Column(db.String(80), nullable=False, default='')
    detail = db.Column(db.Text, nullable=False, default='')
    user = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'user': self.user.public_dict() if self.user else None, 'action': self.action, 'resource_type': self.resource_type, 'resource_id': self.resource_id, 'detail': self.detail, 'created_at': self.created_at.isoformat()}


class PaymentIntent(TimestampMixin, db.Model):
    __tablename__ = 'payment_intents'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = db.Column(db.String(30), nullable=False)
    external_id = db.Column(db.String(180), nullable=False, unique=True)
    checkout_url = db.Column(db.String(500), nullable=False, default='')
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='created')
    invoice = db.relationship('Invoice')

    def to_dict(self):
        return {'id': self.id, 'invoice_id': self.invoice_id, 'provider': self.provider, 'external_id': self.external_id, 'checkout_url': self.checkout_url, 'amount': float(self.amount or 0), 'status': self.status}


class PaymentReconciliation(TimestampMixin, db.Model):
    __tablename__ = 'payment_reconciliations'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False, default='Manual')
    external_id = db.Column(db.String(180), nullable=False, unique=True, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    refunded_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default='Paid')
    refund_status = db.Column(db.String(40), nullable=False, default='Not refunded')
    provider_refund_id = db.Column(db.String(180), nullable=False, default='')
    dispute_reason = db.Column(db.String(255), nullable=False, default='')
    invoice = db.relationship('Invoice')

    def to_dict(self):
        return {'id': self.id, 'invoice_id': self.invoice_id, 'invoice_number': self.invoice.invoice_number if self.invoice else None, 'customer': self.invoice.customer_name if self.invoice else None, 'provider': self.provider, 'external_id': self.external_id, 'amount': float(self.amount or 0), 'refunded_amount': float(self.refunded_amount or 0), 'refundable_amount': float(max((self.amount or 0) - (self.refunded_amount or 0), 0)), 'status': self.status, 'refund_status': self.refund_status, 'provider_refund_id': self.provider_refund_id, 'dispute_reason': self.dispute_reason, 'created_at': self.created_at.isoformat()}


class EInvoice(TimestampMixin, db.Model):
    __tablename__ = 'e_invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    gstin = db.Column(db.String(40), nullable=False, default='')
    place_of_supply = db.Column(db.String(100), nullable=False, default='')
    tax_mode = db.Column(db.String(20), nullable=False, default='CGST/SGST')
    hsn_summary_json = db.Column(db.Text, nullable=False, default='[]')
    cgst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    sgst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    igst_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    irn = db.Column(db.String(120), nullable=False, unique=True)
    acknowledgement_number = db.Column(db.String(80), nullable=False, default='')
    status = db.Column(db.String(40), nullable=False, default='Generated')
    eway_bill_number = db.Column(db.String(80), nullable=False, default='')
    invoice = db.relationship('Invoice')

    def to_dict(self):
        import json
        try: hsn_summary = json.loads(self.hsn_summary_json or '[]')
        except (TypeError, ValueError): hsn_summary = []
        return {'id': self.id, 'invoice_id': self.invoice_id, 'invoice_number': self.invoice.invoice_number if self.invoice else None, 'customer': self.invoice.customer_name if self.invoice else None, 'gstin': self.gstin, 'place_of_supply': self.place_of_supply, 'tax_mode': self.tax_mode, 'hsn_summary': hsn_summary, 'cgst_amount': float(self.cgst_amount or 0), 'sgst_amount': float(self.sgst_amount or 0), 'igst_amount': float(self.igst_amount or 0), 'irn': self.irn, 'acknowledgement_number': self.acknowledgement_number, 'status': self.status, 'eway_bill_number': self.eway_bill_number, 'created_at': self.created_at.isoformat()}


class PaymentOperation(TimestampMixin, db.Model):
    __tablename__ = 'payment_operations'

    id = db.Column(db.Integer, primary_key=True)
    operation_key = db.Column(db.String(180), nullable=False, unique=True, index=True)
    operation_type = db.Column(db.String(40), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False, index=True)
    reconciliation_id = db.Column(db.Integer, db.ForeignKey('payment_reconciliations.id', ondelete='SET NULL'), nullable=True)
    provider = db.Column(db.String(40), nullable=False, default='demo')
    external_id = db.Column(db.String(180), nullable=False, default='')
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default='created')
    message = db.Column(db.Text, nullable=False, default='')
    invoice = db.relationship('Invoice')
    reconciliation = db.relationship('PaymentReconciliation')

    def to_dict(self): return {'id': self.id, 'operation_key': self.operation_key, 'operation_type': self.operation_type, 'invoice_id': self.invoice_id, 'reconciliation_id': self.reconciliation_id, 'provider': self.provider, 'external_id': self.external_id, 'amount': float(self.amount or 0), 'status': self.status, 'message': self.message, 'created_at': self.created_at.isoformat()}


class BackgroundJob(TimestampMixin, db.Model):
    __tablename__ = 'background_jobs'

    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Queued')
    payload_json = db.Column(db.Text, nullable=False, default='{}')
    result_json = db.Column(db.Text, nullable=False, default='{}')
    error = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.relationship('User')

    def to_dict(self):
        import json
        try: payload = json.loads(self.payload_json or '{}'); result = json.loads(self.result_json or '{}')
        except (TypeError, ValueError): payload, result = {}, {}
        return {'id': self.id, 'job_type': self.job_type, 'status': self.status, 'payload': payload, 'result': result, 'error': self.error, 'created_at': self.created_at.isoformat(), 'updated_at': self.updated_at.isoformat()}


class Contract(TimestampMixin, db.Model):
    __tablename__ = 'contracts'

    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    title = db.Column(db.String(180), nullable=False)
    terms = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(40), nullable=False, default='Draft')
    locked = db.Column(db.Boolean, nullable=False, default=False)
    signed_at = db.Column(db.DateTime(timezone=True))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quote = db.relationship('Quote')
    signatures = db.relationship('ContractSignature', back_populates='contract', cascade='all, delete-orphan', lazy='selectin')

    def to_dict(self):
        return {'id': self.id, 'contract_number': self.contract_number, 'quote_id': self.quote_id, 'quote_number': self.quote.quote_number if self.quote else None, 'customer': self.quote.customer_name if self.quote else None, 'title': self.title, 'terms': self.terms, 'status': self.status, 'locked': self.locked, 'signed_at': self.signed_at.isoformat() if self.signed_at else None, 'signatures': [signature.to_dict() for signature in self.signatures]}


class ContractSignature(TimestampMixin, db.Model):
    __tablename__ = 'contract_signatures'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False, index=True)
    signer_name = db.Column(db.String(160), nullable=False)
    signer_email = db.Column(db.String(255), nullable=False, default='')
    signer_role = db.Column(db.String(40), nullable=False, default='client')
    signature_text = db.Column(db.String(255), nullable=False)
    signed_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    ip_address = db.Column(db.String(80), nullable=False, default='')
    contract = db.relationship('Contract', back_populates='signatures')

    def to_dict(self): return {'id': self.id, 'signer_name': self.signer_name, 'signer_email': self.signer_email, 'signer_role': self.signer_role, 'signature_text': self.signature_text, 'signed_at': self.signed_at.isoformat()}


class ProjectSupportTicket(TimestampMixin, db.Model):
    __tablename__ = 'project_support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Open')
    response = db.Column(db.Text, nullable=False, default='')
    order = db.relationship('Order')
    user = db.relationship('User')

    def to_dict(self): return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'subject': self.subject, 'message': self.message, 'status': self.status, 'response': self.response, 'created_at': self.created_at.isoformat(), 'updated_at': self.updated_at.isoformat()}


class DeliverySchedule(TimestampMixin, db.Model):
    __tablename__ = 'delivery_schedules'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    schedule_type = db.Column(db.String(30), nullable=False, default='Delivery')
    scheduled_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(80), nullable=False, default='Morning')
    assigned_team = db.Column(db.String(160), nullable=False, default='')
    eta = db.Column(db.String(80), nullable=False, default='')
    driver_name = db.Column(db.String(120), nullable=False, default='')
    driver_phone = db.Column(db.String(60), nullable=False, default='')
    route_order = db.Column(db.Integer, nullable=False, default=0)
    customer_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(40), nullable=False, default='Scheduled')
    proof_url = db.Column(db.String(500), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')

    def to_dict(self):
        return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.order.customer_name if self.order else None, 'schedule_type': self.schedule_type, 'scheduled_date': self.scheduled_date.isoformat(), 'time_slot': self.time_slot, 'assigned_team': self.assigned_team, 'eta': self.eta, 'driver_name': self.driver_name, 'driver_phone': self.driver_phone, 'route_order': self.route_order, 'customer_confirmed': self.customer_confirmed, 'status': self.status, 'proof_url': self.proof_url, 'notes': self.notes}


class Branch(TimestampMixin, db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    code = db.Column(db.String(30), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False, default='')
    manager = db.Column(db.String(120), nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self): return {'id': self.id, 'name': self.name, 'code': self.code, 'address': self.address, 'manager': self.manager, 'is_active': self.is_active}


class UserBranch(TimestampMixin, db.Model):
    __tablename__ = 'user_branches'
    __table_args__ = (db.UniqueConstraint('user_id', 'branch_id', name='uq_user_branch'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False, index=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User')
    branch = db.relationship('Branch')

    def to_dict(self): return {'id': self.id, 'user_id': self.user_id, 'branch_id': self.branch_id, 'branch': self.branch.to_dict() if self.branch else None, 'is_primary': self.is_primary}


class Tenant(TimestampMixin, db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    plan = db.Column(db.String(40), nullable=False, default='Starter')
    status = db.Column(db.String(30), nullable=False, default='Trial')
    branding_json = db.Column(db.Text, nullable=False, default='{}')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    subscription = db.relationship('Subscription', back_populates='tenant', uselist=False, cascade='all, delete-orphan')
    def to_dict(self):
        try: branding = json.loads(self.branding_json or '{}')
        except (TypeError, ValueError): branding = {}
        return {'id': self.id, 'name': self.name, 'slug': self.slug, 'plan': self.plan, 'status': self.status, 'branding': branding, 'is_active': self.is_active}


class TenantMembership(TimestampMixin, db.Model):
    __tablename__ = 'tenant_memberships'
    __table_args__ = (db.UniqueConstraint('tenant_id', 'user_id', name='uq_tenant_user'),)
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(40), nullable=False, default='Member')
    status = db.Column(db.String(30), nullable=False, default='Active')
    tenant = db.relationship('Tenant')
    user = db.relationship('User')
    def to_dict(self): return {'id': self.id, 'tenant_id': self.tenant_id, 'tenant': self.tenant.to_dict() if self.tenant else None, 'user_id': self.user_id, 'user': self.user.public_dict() if self.user else None, 'role': self.role, 'status': self.status}


class Subscription(TimestampMixin, db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    provider = db.Column(db.String(40), nullable=False, default='demo')
    external_id = db.Column(db.String(180), nullable=False, default='')
    plan = db.Column(db.String(40), nullable=False, default='Starter')
    status = db.Column(db.String(30), nullable=False, default='trialing')
    seats = db.Column(db.Integer, nullable=False, default=5)
    monthly_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    current_period_end = db.Column(db.Date)
    tenant = db.relationship('Tenant', back_populates='subscription')
    def to_dict(self): return {'id': self.id, 'tenant_id': self.tenant_id, 'provider': self.provider, 'external_id': self.external_id, 'plan': self.plan, 'status': self.status, 'seats': self.seats, 'monthly_amount': float(self.monthly_amount or 0), 'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None}

class Warehouse(TimestampMixin, db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True, index=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False, default='')
    manager = db.Column(db.String(120), nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    branch = db.relationship('Branch')

    def to_dict(self): return {'id': self.id, 'name': self.name, 'address': self.address, 'manager': self.manager, 'branch_id': self.branch_id, 'branch': self.branch.name if self.branch else None, 'is_active': self.is_active}


class WarehouseStock(TimestampMixin, db.Model):
    __tablename__ = 'warehouse_stock'
    __table_args__ = (db.UniqueConstraint('warehouse_id', 'product_id', 'variant_id', name='uq_warehouse_stock_selection'),)

    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    reserved_quantity = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    warehouse = db.relationship('Warehouse')
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')

    def to_dict(self): return {'id': self.id, 'warehouse_id': self.warehouse_id, 'warehouse': self.warehouse.name if self.warehouse else None, 'product_id': self.product_id, 'product': self.product.name if self.product else None, 'sku': self.variant.sku if self.variant else self.product.sku if self.product else None, 'quantity': float(self.quantity or 0), 'reserved_quantity': float(self.reserved_quantity or 0), 'available_quantity': float(max((self.quantity or 0) - (self.reserved_quantity or 0), 0))}


class StockMovement(TimestampMixin, db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    movement_type = db.Column(db.String(40), nullable=False, default='Transfer')
    reference = db.Column(db.String(120), nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product = db.relationship('Product')
    from_warehouse = db.relationship('Warehouse', foreign_keys=[from_warehouse_id])
    to_warehouse = db.relationship('Warehouse', foreign_keys=[to_warehouse_id])

    def to_dict(self): return {'id': self.id, 'from_warehouse': self.from_warehouse.name if self.from_warehouse else None, 'to_warehouse': self.to_warehouse.name if self.to_warehouse else None, 'product': self.product.name if self.product else None, 'quantity': float(self.quantity or 0), 'movement_type': self.movement_type, 'reference': self.reference, 'created_at': self.created_at.isoformat()}


class ReturnRequest(TimestampMixin, db.Model):
    __tablename__ = 'return_requests'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True, index=True)
    customer_name = db.Column(db.String(180), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default='Requested')
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')
    invoice = db.relationship('Invoice')
    credit_note = db.relationship('CreditNote', back_populates='return_request', uselist=False, cascade='all, delete-orphan')

    def to_dict(self): return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'invoice_id': self.invoice_id, 'customer': self.customer_name, 'reason': self.reason, 'amount': float(self.amount or 0), 'status': self.status, 'notes': self.notes, 'credit_note': self.credit_note.to_dict() if self.credit_note else None, 'created_at': self.created_at.isoformat()}


class CreditNote(TimestampMixin, db.Model):
    __tablename__ = 'credit_notes'

    id = db.Column(db.Integer, primary_key=True)
    credit_note_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    return_request_id = db.Column(db.Integer, db.ForeignKey('return_requests.id', ondelete='CASCADE'), nullable=False, unique=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Issued')
    return_request = db.relationship('ReturnRequest', back_populates='credit_note')

    def to_dict(self): return {'id': self.id, 'credit_note_number': self.credit_note_number, 'amount': float(self.amount or 0), 'status': self.status}


class QuotePreset(TimestampMixin, db.Model):
    __tablename__ = 'quote_presets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    kind = db.Column(db.String(40), nullable=False, default='Template')
    room = db.Column(db.String(100), nullable=False, default='')
    description = db.Column(db.Text, nullable=False, default='')
    discount_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    items_json = db.Column(db.Text, nullable=False, default='[]')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User')

    def to_dict(self):
        import json
        try:
            items = json.loads(self.items_json or '[]')
        except (TypeError, ValueError):
            items = []
        return {'id': self.id, 'name': self.name, 'kind': self.kind, 'room': self.room, 'description': self.description, 'discount_percent': float(self.discount_percent or 0), 'items': items}


class CustomerPricing(TimestampMixin, db.Model):
    __tablename__ = 'customer_pricing'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    tier = db.Column(db.String(40), nullable=False, default='Standard')
    discount_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    customer = db.relationship('Customer')

    def to_dict(self): return {'id': self.id, 'customer_id': self.customer_id, 'customer': self.customer.company if self.customer else None, 'tier': self.tier, 'discount_percent': float(self.discount_percent or 0)}


class ProductionJob(TimestampMixin, db.Model):
    __tablename__ = 'production_jobs'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    job_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default='Planned')
    scheduled_start = db.Column(db.Date)
    due_date = db.Column(db.Date)
    assigned_team = db.Column(db.String(160), nullable=False, default='')
    wastage_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')
    bom_items = db.relationship('BomItem', back_populates='production_job', cascade='all, delete-orphan', lazy='selectin')
    tasks = db.relationship('ProductionTask', back_populates='production_job', cascade='all, delete-orphan', lazy='selectin')
    inspections = db.relationship('QualityInspection', back_populates='production_job', cascade='all, delete-orphan', lazy='selectin')

    def to_dict(self):
        return {'id': self.id, 'job_number': self.job_number, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.order.customer_name if self.order else None, 'status': self.status, 'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None, 'due_date': self.due_date.isoformat() if self.due_date else None, 'assigned_team': self.assigned_team, 'wastage_percent': float(self.wastage_percent or 0), 'notes': self.notes, 'bom_items': [item.to_dict() for item in self.bom_items], 'tasks': [item.to_dict() for item in self.tasks], 'inspections': [item.to_dict() for item in self.inspections]}


class BomItem(TimestampMixin, db.Model):
    __tablename__ = 'bom_items'

    id = db.Column(db.Integer, primary_key=True)
    production_job_id = db.Column(db.Integer, db.ForeignKey('production_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    unit = db.Column(db.String(40), nullable=False, default='piece')
    wastage_percent = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    labor_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default='Required')
    production_job = db.relationship('ProductionJob', back_populates='bom_items')
    product = db.relationship('Product')

    def to_dict(self):
        planned_quantity = (self.quantity or 0) * (1 + (self.wastage_percent or 0) / 100)
        return {'id': self.id, 'product_id': self.product_id, 'product': self.product.name if self.product else None, 'description': self.description, 'quantity': float(self.quantity or 0), 'unit': self.unit, 'wastage_percent': float(self.wastage_percent or 0), 'planned_quantity': float(planned_quantity), 'unit_cost': float(self.unit_cost or 0), 'labor_cost': float(self.labor_cost or 0), 'material_cost': float(planned_quantity * (self.unit_cost or 0)), 'total_cost': float((planned_quantity * (self.unit_cost or 0)) + (self.labor_cost or 0)), 'status': self.status}


class ProductionTask(TimestampMixin, db.Model):
    __tablename__ = 'production_tasks'

    id = db.Column(db.Integer, primary_key=True)
    production_job_id = db.Column(db.Integer, db.ForeignKey('production_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    stage = db.Column(db.String(60), nullable=False, default='Assembly')
    assigned_worker = db.Column(db.String(120), nullable=False, default='')
    machine = db.Column(db.String(120), nullable=False, default='')
    dependency_id = db.Column(db.Integer, db.ForeignKey('production_tasks.id'), nullable=True)
    planned_start = db.Column(db.DateTime(timezone=True))
    planned_end = db.Column(db.DateTime(timezone=True))
    actual_minutes = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(40), nullable=False, default='Planned')
    production_job = db.relationship('ProductionJob', back_populates='tasks')
    dependency = db.relationship('ProductionTask', remote_side=[id])

    def to_dict(self): return {'id': self.id, 'production_job_id': self.production_job_id, 'job_number': self.production_job.job_number if self.production_job else None, 'name': self.name, 'stage': self.stage, 'assigned_worker': self.assigned_worker, 'machine': self.machine, 'dependency_id': self.dependency_id, 'planned_start': self.planned_start.isoformat() if self.planned_start else None, 'planned_end': self.planned_end.isoformat() if self.planned_end else None, 'actual_minutes': self.actual_minutes, 'status': self.status}


class QualityInspection(TimestampMixin, db.Model):
    __tablename__ = 'quality_inspections'

    id = db.Column(db.Integer, primary_key=True)
    production_job_id = db.Column(db.Integer, db.ForeignKey('production_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(40), nullable=False, default='Pending')
    checklist_json = db.Column(db.Text, nullable=False, default='[]')
    defects_json = db.Column(db.Text, nullable=False, default='[]')
    photo_url = db.Column(db.String(500), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False, default='')
    rework_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    approved_at = db.Column(db.DateTime(timezone=True))
    production_job = db.relationship('ProductionJob', back_populates='inspections')
    inspector = db.relationship('User')

    def to_dict(self):
        try: checklist = json.loads(self.checklist_json or '[]'); defects = json.loads(self.defects_json or '[]')
        except (TypeError, ValueError): checklist, defects = [], []
        return {'id': self.id, 'production_job_id': self.production_job_id, 'job_number': self.production_job.job_number if self.production_job else None, 'inspector': self.inspector.public_dict() if self.inspector else None, 'status': self.status, 'checklist': checklist, 'defects': defects, 'photo_url': self.photo_url, 'notes': self.notes, 'rework_cost': float(self.rework_cost or 0), 'approved_at': self.approved_at.isoformat() if self.approved_at else None}


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


class MediaAsset(TimestampMixin, db.Model):
    __tablename__ = 'media_assets'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(40), nullable=False, default='local')
    public_id = db.Column(db.String(255), nullable=False, default='')
    url = db.Column(db.String(1000), nullable=False)
    resource_type = db.Column(db.String(30), nullable=False, default='image')
    folder = db.Column(db.String(255), nullable=False, default='')
    entity_type = db.Column(db.String(60), nullable=False, default='unlinked')
    entity_id = db.Column(db.String(120), nullable=False, default='')
    original_filename = db.Column(db.String(255), nullable=False, default='')
    bytes = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    uploaded_by = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'provider': self.provider, 'public_id': self.public_id, 'url': self.url, 'resource_type': self.resource_type, 'folder': self.folder, 'entity_type': self.entity_type, 'entity_id': self.entity_id, 'original_filename': self.original_filename, 'bytes': self.bytes, 'is_active': self.is_active, 'uploaded_by': self.uploaded_by.public_dict() if self.uploaded_by else None, 'created_at': self.created_at.isoformat()}


class FieldVisit(TimestampMixin, db.Model):
    __tablename__ = 'field_visits'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('delivery_schedules.id'), nullable=True)
    visit_type = db.Column(db.String(40), nullable=False, default='Installation')
    status = db.Column(db.String(40), nullable=False, default='Scheduled', index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    qr_token = db.Column(db.String(80), unique=True, nullable=False, index=True)
    proof_photo_url = db.Column(db.String(500), nullable=False, default='')
    customer_signature = db.Column(db.String(255), nullable=False, default='')
    gps_lat = db.Column(db.Numeric(10, 7))
    gps_lng = db.Column(db.Numeric(10, 7))
    check_in_at = db.Column(db.DateTime(timezone=True))
    check_out_at = db.Column(db.DateTime(timezone=True))
    time_minutes = db.Column(db.Integer, nullable=False, default=0)
    materials_json = db.Column(db.Text, nullable=False, default='[]')
    notes = db.Column(db.Text, nullable=False, default='')
    offline_synced = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')
    schedule = db.relationship('DeliverySchedule')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def to_dict(self):
        try: materials = json.loads(self.materials_json or '[]')
        except (TypeError, ValueError): materials = []
        return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.order.customer_name if self.order else None, 'schedule_id': self.schedule_id, 'visit_type': self.visit_type, 'status': self.status, 'assigned_to_id': self.assigned_to_id, 'assigned_to': self.assigned_to.public_dict() if self.assigned_to else None, 'scheduled_date': self.scheduled_date.isoformat(), 'qr_token': self.qr_token, 'proof_photo_url': self.proof_photo_url, 'customer_signature': self.customer_signature, 'gps_lat': float(self.gps_lat) if self.gps_lat is not None else None, 'gps_lng': float(self.gps_lng) if self.gps_lng is not None else None, 'check_in_at': self.check_in_at.isoformat() if self.check_in_at else None, 'check_out_at': self.check_out_at.isoformat() if self.check_out_at else None, 'time_minutes': self.time_minutes, 'materials': materials, 'notes': self.notes, 'offline_synced': self.offline_synced}


class IntegrationConnection(TimestampMixin, db.Model):
    __tablename__ = 'integration_connections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    provider = db.Column(db.String(40), nullable=False, index=True)
    base_url = db.Column(db.String(255), nullable=False, default='')
    external_account = db.Column(db.String(160), nullable=False, default='')
    credentials_ref = db.Column(db.String(255), nullable=False, default='')
    status = db.Column(db.String(30), nullable=False, default='Not connected')
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_sync_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'provider': self.provider, 'base_url': self.base_url, 'external_account': self.external_account, 'credentials_ref': self.credentials_ref, 'status': self.status, 'is_enabled': self.is_enabled, 'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None}


class SyncRun(TimestampMixin, db.Model):
    __tablename__ = 'sync_runs'

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('integration_connections.id', ondelete='CASCADE'), nullable=False, index=True)
    entity = db.Column(db.String(60), nullable=False, default='invoices')
    status = db.Column(db.String(30), nullable=False, default='Queued')
    records_synced = db.Column(db.Integer, nullable=False, default=0)
    error = db.Column(db.Text, nullable=False, default='')
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True))
    connection = db.relationship('IntegrationConnection')

    def to_dict(self):
        return {'id': self.id, 'connection_id': self.connection_id, 'provider': self.connection.provider if self.connection else None, 'entity': self.entity, 'status': self.status, 'records_synced': self.records_synced, 'error': self.error, 'started_at': self.started_at.isoformat(), 'completed_at': self.completed_at.isoformat() if self.completed_at else None}


class Warranty(TimestampMixin, db.Model):
    __tablename__ = 'warranties'

    id = db.Column(db.Integer, primary_key=True)
    warranty_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    coverage = db.Column(db.String(255), nullable=False, default='Manufacturing defects and installation issues')
    status = db.Column(db.String(30), nullable=False, default='Active', index=True)
    serial_number = db.Column(db.String(100), nullable=False, default='')
    order = db.relationship('Order')
    product = db.relationship('Product')
    customer = db.relationship('Customer')

    def to_dict(self):
        return {'id': self.id, 'warranty_number': self.warranty_number, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.customer.company if self.customer else (self.order.customer_name if self.order else None), 'product_id': self.product_id, 'product': self.product.name if self.product else None, 'start_date': self.start_date.isoformat(), 'end_date': self.end_date.isoformat(), 'coverage': self.coverage, 'status': self.status, 'serial_number': self.serial_number}


class ServiceTicket(TimestampMixin, db.Model):
    __tablename__ = 'service_tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warranty_id = db.Column(db.Integer, db.ForeignKey('warranties.id'), nullable=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    subject = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(30), nullable=False, default='Normal')
    status = db.Column(db.String(40), nullable=False, default='Open', index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    sla_due = db.Column(db.Date)
    visit_date = db.Column(db.Date)
    parts_used = db.Column(db.Text, nullable=False, default='')
    technician_minutes = db.Column(db.Integer, nullable=False, default=0)
    customer_rating = db.Column(db.Integer, nullable=False, default=0)
    customer_feedback = db.Column(db.Text, nullable=False, default='')
    resolution = db.Column(db.Text, nullable=False, default='')
    warranty = db.relationship('Warranty')
    order = db.relationship('Order')
    customer = db.relationship('Customer')
    assigned_to = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'ticket_number': self.ticket_number, 'warranty_id': self.warranty_id, 'warranty_number': self.warranty.warranty_number if self.warranty else None, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.customer.company if self.customer else (self.order.customer_name if self.order else None), 'subject': self.subject, 'description': self.description, 'priority': self.priority, 'status': self.status, 'assigned_to_id': self.assigned_to_id, 'assigned_to': self.assigned_to.public_dict() if self.assigned_to else None, 'sla_due': self.sla_due.isoformat() if self.sla_due else None, 'visit_date': self.visit_date.isoformat() if self.visit_date else None, 'parts_used': self.parts_used, 'technician_minutes': self.technician_minutes, 'customer_rating': self.customer_rating, 'customer_feedback': self.customer_feedback, 'resolution': self.resolution, 'created_at': self.created_at.isoformat(), 'updated_at': self.updated_at.isoformat()}


class Department(TimestampMixin, db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description, 'is_active': self.is_active}


class UserDepartment(TimestampMixin, db.Model):
    __tablename__ = 'user_departments'
    __table_args__ = (db.UniqueConstraint('user_id', 'department_id', name='uq_user_department'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False, index=True)
    role_title = db.Column(db.String(100), nullable=False, default='Member')
    user = db.relationship('User')
    department = db.relationship('Department')

    def to_dict(self):
        return {'id': self.id, 'user_id': self.user_id, 'user': self.user.public_dict() if self.user else None, 'department_id': self.department_id, 'department': self.department.name if self.department else None, 'role_title': self.role_title}


class AccessPermission(TimestampMixin, db.Model):
    __tablename__ = 'access_permissions'
    __table_args__ = (db.UniqueConstraint('user_id', 'permission', 'scope', name='uq_user_permission_scope'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    permission = db.Column(db.String(120), nullable=False)
    scope = db.Column(db.String(80), nullable=False, default='own')
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    user = db.relationship('User')

    def to_dict(self):
        return {'id': self.id, 'user_id': self.user_id, 'permission': self.permission, 'scope': self.scope, 'is_enabled': self.is_enabled}


class ProjectOwnership(TimestampMixin, db.Model):
    __tablename__ = 'project_ownerships'
    __table_args__ = (db.UniqueConstraint('order_id', 'user_id', name='uq_project_owner'),)

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')
    user = db.relationship('User', foreign_keys=[user_id])
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])

    def to_dict(self):
        return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.order.customer_name if self.order else None, 'user_id': self.user_id, 'owner': self.user.public_dict() if self.user else None, 'assigned_by': self.assigned_by.name if self.assigned_by else None}


class ApprovalRequest(TimestampMixin, db.Model):
    __tablename__ = 'approval_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(60), nullable=False, index=True)
    resource_type = db.Column(db.String(60), nullable=False)
    resource_id = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    detail = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(30), nullable=False, default='Requested', index=True)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    def to_dict(self):
        return {'id': self.id, 'request_type': self.request_type, 'resource_type': self.resource_type, 'resource_id': self.resource_id, 'amount': float(self.amount or 0), 'detail': self.detail, 'status': self.status, 'requested_by': self.requested_by.public_dict() if self.requested_by else None, 'approved_by': self.approved_by.public_dict() if self.approved_by else None, 'created_at': self.created_at.isoformat(), 'updated_at': self.updated_at.isoformat()}
