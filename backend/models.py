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
    notification = db.relationship('Notification')

    def to_dict(self):
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'channel': self.channel,
            'recipient': self.recipient,
            'status': self.status,
            'error': self.error,
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
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    payment_link = db.Column(db.String(500), nullable=False, default='')
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
            'subtotal': float(self.subtotal or 0),
            'tax_amount': float(self.tax_amount or 0),
            'total': float(self.total or 0),
            'amount_paid': float(self.amount_paid or 0),
            'balance': float(self.balance),
            'payment_link': self.payment_link,
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
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    supplier = db.relationship('Supplier')
    items = db.relationship('PurchaseOrderItem', back_populates='purchase_order', cascade='all, delete-orphan', lazy='selectin')

    @property
    def total(self):
        return sum((item.line_total for item in self.items), 0)

    def to_dict(self):
        return {'id': self.id, 'po_number': self.po_number, 'supplier_id': self.supplier_id, 'supplier': self.supplier.name if self.supplier else None, 'status': self.status, 'order_date': self.order_date.isoformat(), 'expected_date': self.expected_date.isoformat() if self.expected_date else None, 'notes': self.notes, 'total': float(self.total), 'items': [item.to_dict() for item in self.items]}


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


class DeliverySchedule(TimestampMixin, db.Model):
    __tablename__ = 'delivery_schedules'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    schedule_type = db.Column(db.String(30), nullable=False, default='Delivery')
    scheduled_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(80), nullable=False, default='Morning')
    assigned_team = db.Column(db.String(160), nullable=False, default='')
    status = db.Column(db.String(40), nullable=False, default='Scheduled')
    proof_url = db.Column(db.String(500), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False, default='')
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order = db.relationship('Order')

    def to_dict(self):
        return {'id': self.id, 'order_id': self.order_id, 'order_number': self.order.order_number if self.order else None, 'customer': self.order.customer_name if self.order else None, 'schedule_type': self.schedule_type, 'scheduled_date': self.scheduled_date.isoformat(), 'time_slot': self.time_slot, 'assigned_team': self.assigned_team, 'status': self.status, 'proof_url': self.proof_url, 'notes': self.notes}

class Warehouse(TimestampMixin, db.Model):
    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False, default='')
    manager = db.Column(db.String(120), nullable=False, default='')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self): return {'id': self.id, 'name': self.name, 'address': self.address, 'manager': self.manager, 'is_active': self.is_active}


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
