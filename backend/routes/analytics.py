from collections import defaultdict
from flask import Blueprint, jsonify
from ..extensions import db
from decimal import Decimal
from ..models import InventoryItem, Invoice, Lead, Order, ProductionJob, Quote
from ..utils import roles_required

analytics_bp = Blueprint('analytics', __name__)


def _unit_cost(product):
    if not product:
        return Decimal('0')
    if product.cost_price and product.cost_price > 0:
        return Decimal(str(product.cost_price))
    return Decimal(str(product.price or 0)) * Decimal('0.45')


def _job_cost(job):
    total = Decimal('0')
    for item in job.bom_items:
        planned = Decimal(str(item.quantity or 0)) * (Decimal('1') + Decimal(str(item.wastage_percent or 0)) / 100)
        unit_cost = Decimal(str(item.unit_cost or 0)) or _unit_cost(item.product)
        material_cost = planned * unit_cost
        labor_cost = Decimal(str(item.labor_cost or 0)) or material_cost * Decimal('0.18')
        total += material_cost + labor_cost
    return total


@analytics_bp.get('')
@roles_required('admin', 'sales', 'designer')
def analytics_dashboard():
    quotes = db.session.scalars(db.select(Quote)).all()
    invoices = db.session.scalars(db.select(Invoice)).all()
    leads = db.session.scalars(db.select(Lead)).all()
    stock = db.session.scalars(db.select(InventoryItem)).all()
    jobs = db.session.scalars(db.select(ProductionJob)).all()
    orders = db.session.scalars(db.select(Order)).all()
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
    job_by_quote = {job.order.quote_id: job for job in jobs if job.order}
    profitability_rows = []
    product_profitability = defaultdict(lambda: {'product': '', 'revenue': 0, 'estimated_cost': 0, 'quantity': 0})
    profitability_revenue = Decimal('0'); profitability_cost = Decimal('0')
    for order in orders:
        if not order.quote: continue
        order_revenue = Decimal(str(order.quote.total or 0))
        job = job_by_quote.get(order.quote_id)
        if job:
            order_cost = _job_cost(job)
        else:
            order_cost = sum((Decimal(str(item.quantity or 0)) * _unit_cost(item.product) * Decimal('1.18') for item in order.quote.items), Decimal('0'))
        profitability_revenue += order_revenue; profitability_cost += order_cost
        profitability_rows.append({'order_number': order.order_number, 'customer': order.customer_name, 'revenue': float(order_revenue), 'estimated_cost': float(order_cost), 'gross_profit': float(order_revenue - order_cost), 'margin_percent': round(float((order_revenue - order_cost) / order_revenue * 100) if order_revenue else 0, 1)})
        for item in order.quote.items:
            product = item.product
            name = product.name if product else item.description
            row = product_profitability[name]; row['product'] = name; row['revenue'] += float(item.line_total); row['quantity'] += float(item.quantity or 0); row['estimated_cost'] += float(Decimal(str(item.quantity or 0)) * _unit_cost(product))
    gross_profit = profitability_revenue - profitability_cost
    for row in product_profitability.values(): row['gross_profit'] = round(row['revenue'] - row['estimated_cost'], 2); row['margin_percent'] = round((row['gross_profit'] / row['revenue'] * 100) if row['revenue'] else 0, 1)
    return jsonify({'summary': {'revenue': round(revenue, 2), 'invoice_total': round(invoice_total, 2), 'outstanding': round(max(invoice_total - revenue, 0), 2), 'quote_pipeline': round(quote_pipeline, 2), 'conversion_rate': round((len(approved_quotes) / len(quotes) * 100) if quotes else 0, 1), 'lead_win_rate': round((len(won_leads) / len(leads) * 100) if leads else 0, 1), 'inventory_value': round(sum(float(item.quantity or 0) * float(item.product.price or 0) for item in stock if item.product), 2), 'low_stock': sum(1 for item in stock if (item.quantity or 0) - (item.reserved_quantity or 0) <= (item.reorder_level or 0))}, 'profitability': {'revenue': float(profitability_revenue), 'estimated_cost': float(profitability_cost), 'gross_profit': float(gross_profit), 'margin_percent': round(float(gross_profit / profitability_revenue * 100) if profitability_revenue else 0, 1), 'projects': profitability_rows, 'top_products': sorted(product_profitability.values(), key=lambda item: item['gross_profit'], reverse=True)[:8]}, 'quotes_by_status': _counts(quotes, 'status'), 'leads_by_stage': _counts(leads, 'stage'), 'production_by_status': _counts(jobs, 'status'), 'forecast': {'next_30_days': round(revenue + (quote_pipeline * 0.35), 2), 'next_90_days': round(revenue + (quote_pipeline * 0.75), 2), 'method': 'Collected revenue plus weighted open pipeline'}, 'top_customers': top_customers, 'mode': 'api'})


def _counts(items, field):
    counts = defaultdict(int)
    for item in items:
        counts[getattr(item, field) or 'Unknown'] += 1
    return [{'label': label, 'count': count} for label, count in sorted(counts.items())]
