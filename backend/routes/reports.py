from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from ..extensions import db
from ..models import InventoryItem, Invoice, Lead, Order, Payment, Quote
from ..utils import roles_required

reports_bp = Blueprint('reports', __name__)
REPORT_METRICS = {'quotes', 'leads', 'orders', 'invoices', 'payments', 'inventory', 'profitability', 'forecast'}


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


@reports_bp.get('/custom')
@roles_required('admin', 'sales')
def custom_report():
    selected = [item.strip() for item in str(request.args.get('metrics', 'quotes,orders,invoices,inventory')).split(',') if item.strip()]
    selected = [item for item in selected if item in REPORT_METRICS]
    if not selected: return jsonify({'message': 'Choose at least one supported report metric.'}), 400
    try: period_days = min(max(int(request.args.get('period_days', 90)), 7), 3650)
    except (TypeError, ValueError): return jsonify({'message': 'Period must be a valid number of days.'}), 400
    summary_data = summary().get_json()['data']
    invoices = db.session.scalars(db.select(Invoice)).all(); orders = db.session.scalars(db.select(Order)).all()
    revenue = sum(float(item.amount_paid or 0) for item in invoices)
    invoice_total = sum(float(item.total or 0) for item in invoices)
    estimated_cost = sum(float(item.total or 0) * 0.55 for item in invoices)
    metrics = {key: summary_data[key] for key in selected if key in summary_data}
    if 'profitability' in selected: metrics['profitability'] = {'revenue': round(revenue, 2), 'estimated_cost': round(estimated_cost, 2), 'gross_profit': round(revenue - estimated_cost, 2), 'margin_percent': round((revenue - estimated_cost) / revenue * 100, 1) if revenue else 0, 'note': 'Management estimate; use the analytics dashboard for BOM-level cost detail.'}
    if 'forecast' in selected: metrics['forecast'] = {'next_30_days': round(revenue + max(invoice_total - revenue, 0) * 0.35, 2), 'next_90_days': round(revenue + max(invoice_total - revenue, 0) * 0.75, 2), 'confidence_percent': 70, 'method': 'Collected revenue plus outstanding invoice pipeline'}
    return jsonify({'report': {'metrics': metrics, 'selected_metrics': selected, 'period_days': period_days, 'filters': {'scope': 'current workspace'}, 'generated_at': datetime.now(timezone.utc).isoformat(), 'export_formats': ['csv', 'pdf', 'xlsx']}, 'mode': 'api'})
