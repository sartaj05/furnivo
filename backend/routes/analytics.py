from collections import defaultdict
from flask import Blueprint, jsonify
from ..extensions import db
from ..models import InventoryItem, Invoice, Lead, ProductionJob, Quote
from ..utils import roles_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.get('')
@roles_required('admin', 'sales', 'designer')
def analytics_dashboard():
    quotes = db.session.scalars(db.select(Quote)).all()
    invoices = db.session.scalars(db.select(Invoice)).all()
    leads = db.session.scalars(db.select(Lead)).all()
    stock = db.session.scalars(db.select(InventoryItem)).all()
    jobs = db.session.scalars(db.select(ProductionJob)).all()
    revenue = sum(float(item.amount_paid or 0) for item in invoices)
    invoice_total = sum(float(item.total or 0) for item in invoices)
    open_quotes = [item for item in quotes if item.status not in {'Approved', 'Rejected', 'Expired'}]
    approved_quotes = [item for item in quotes if item.status == 'Approved']
    quote_pipeline = sum(float(item.total or 0) for item in open_quotes)
    quote_value = sum(float(item.total or 0) for item in quotes)
    won_leads = [item for item in leads if item.stage == 'Won']
    customer_values = defaultdict(float)
    for item in invoices:
        customer_values[item.customer_name] += float(item.total or 0)
    top_customers = [{'customer': name, 'value': round(value, 2)} for name, value in sorted(customer_values.items(), key=lambda pair: pair[1], reverse=True)[:5]]
    return jsonify({'summary': {'revenue': round(revenue, 2), 'invoice_total': round(invoice_total, 2), 'outstanding': round(max(invoice_total - revenue, 0), 2), 'quote_pipeline': round(quote_pipeline, 2), 'conversion_rate': round((len(approved_quotes) / len(quotes) * 100) if quotes else 0, 1), 'lead_win_rate': round((len(won_leads) / len(leads) * 100) if leads else 0, 1), 'inventory_value': round(sum(float(item.quantity or 0) * float(item.product.price or 0) for item in stock if item.product), 2), 'low_stock': sum(1 for item in stock if (item.quantity or 0) - (item.reserved_quantity or 0) <= (item.reorder_level or 0))}, 'quotes_by_status': _counts(quotes, 'status'), 'leads_by_stage': _counts(leads, 'stage'), 'production_by_status': _counts(jobs, 'status'), 'forecast': {'next_30_days': round(revenue + (quote_pipeline * 0.35), 2), 'next_90_days': round(revenue + (quote_pipeline * 0.75), 2), 'method': 'Collected revenue plus weighted open pipeline'}, 'top_customers': top_customers, 'mode': 'api'})


def _counts(items, field):
    counts = defaultdict(int)
    for item in items:
        counts[getattr(item, field) or 'Unknown'] += 1
    return [{'label': label, 'count': count} for label, count in sorted(counts.items())]
