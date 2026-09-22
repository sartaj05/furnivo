from flask import Blueprint, jsonify
from sqlalchemy import func
from ..extensions import db
from ..models import InventoryItem, Invoice, Lead, Order, Payment, Quote
from ..utils import roles_required

reports_bp = Blueprint('reports', __name__)


@reports_bp.get('/summary')
@roles_required('admin', 'sales')
def summary():
    quotes = db.session.scalars(db.select(Quote)).all()
    leads = db.session.scalars(db.select(Lead)).all()
    orders = db.session.scalars(db.select(Order)).all()
    invoices = db.session.scalars(db.select(Invoice)).all()
    inventory = db.session.scalars(db.select(InventoryItem)).all()
    payments = db.session.scalars(db.select(Payment)).all()
    return jsonify({'data': {
        'quotes': {'count': len(quotes), 'value': float(sum((item.total for item in quotes), 0))},
        'leads': {'count': len(leads), 'value': float(sum((item.value for item in leads), 0)), 'won': sum(1 for item in leads if item.stage == 'Won')},
        'orders': {'count': len(orders), 'value': float(sum((item.quote.total for item in orders if item.quote), 0))},
        'invoices': {'count': len(invoices), 'value': float(sum((item.total for item in invoices), 0)), 'paid': float(sum((item.amount_paid for item in invoices), 0)), 'balance': float(sum((item.balance for item in invoices), 0))},
        'payments': {'count': len(payments), 'value': float(sum((item.amount for item in payments), 0))},
        'inventory': {'items': len(inventory), 'low_stock': sum(1 for item in inventory if item.is_low_stock), 'available_units': float(sum((item.available_quantity for item in inventory), 0))},
    }, 'mode': 'api'})
