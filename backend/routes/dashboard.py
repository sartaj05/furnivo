from flask import Blueprint, jsonify
from ..extensions import db
from ..models import Invoice, Lead, Order, ProductionJob, Product, Quote, QuoteClientAccess
from ..utils import assigned_order_ids, current_user, roles_required

dashboard_bp = Blueprint('dashboard', __name__)


def card(key, label, value, helper, display=None):
    return {'key': key, 'label': label, 'value': value, 'display': display if display is not None else str(value), 'helper': helper}


@dashboard_bp.get('/metrics')
@roles_required('admin', 'sales', 'designer', 'client')
def role_metrics():
    user = current_user()
    products = db.session.scalar(db.select(db.func.count(Product.id)).where(Product.is_active.is_(True))) or 0
    if user.role == 'admin':
        quotes = db.session.scalars(db.select(Quote)).all()
        leads = db.session.scalars(db.select(Lead)).all()
        invoices = db.session.scalars(db.select(Invoice)).all()
        pipeline = sum(float(item.total or 0) for item in quotes if item.status not in {'Approved', 'Rejected', 'Expired'})
        revenue = sum(float(item.amount_paid or 0) for item in invoices)
        cards = [card('products', 'Catalog products', products, 'Active catalog products'), card('quotes', 'Open quotations', sum(item.status not in {'Approved', 'Rejected', 'Expired'} for item in quotes), 'Current quotation pipeline'), card('leads', 'Active leads', sum(item.stage not in {'Won', 'Lost'} for item in leads), 'Open commercial opportunities'), card('revenue', 'Collected revenue', revenue, 'Payments received', f'₹{revenue:,.0f}')]
        focus = f'₹{pipeline:,.0f} remains in the open quotation pipeline.'
    elif user.role == 'sales':
        order_ids = assigned_order_ids(user.id)
        quote_ids = db.session.scalars(db.select(Order.quote_id).where(Order.id.in_(order_ids or [-1]))).all()
        quotes = db.session.scalars(db.select(Quote).where((Quote.created_by_id == user.id) | Quote.id.in_(quote_ids or [-1]))).all()
        leads = db.session.scalars(db.select(Lead).where(Lead.owner_id == user.id)).all()
        pipeline = sum(float(item.total or 0) for item in quotes if item.status not in {'Approved', 'Rejected', 'Expired'})
        followups = sum(sum(not task.is_done for task in lead.tasks) for lead in leads)
        cards = [card('quotes', 'Open quotations', sum(item.status not in {'Approved', 'Rejected', 'Expired'} for item in quotes), 'Assigned or created by you'), card('pipeline', 'Pipeline value', pipeline, 'Open quotation value', f'₹{pipeline:,.0f}'), card('leads', 'Active leads', sum(item.stage not in {'Won', 'Lost'} for item in leads), 'Owned opportunities'), card('followups', 'Open follow-ups', followups, 'Tasks needing attention')]
        focus = f'{followups} follow-up task(s) need attention.'
    elif user.role == 'designer':
        order_ids = assigned_order_ids(user.id)
        jobs = db.session.scalars(db.select(ProductionJob).where(ProductionJob.order_id.in_(order_ids or [-1]))).all()
        active = sum(item.status not in {'Complete', 'On hold'} for item in jobs)
        quality = sum(item.status == 'Quality check' for item in jobs)
        cards = [card('projects', 'Assigned projects', len(order_ids), 'Projects assigned to you'), card('production', 'Active production', active, 'Jobs in execution'), card('quality', 'Quality checks', quality, 'Jobs awaiting inspection'), card('products', 'Catalog products', products, 'Reference library')]
        focus = f'{quality} production job(s) are waiting for quality review.'
    else:
        quote_ids = db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == user.id)).all()
        orders = db.session.scalars(db.select(Order).where(Order.quote_id.in_(quote_ids or [-1]))).all()
        cards = [card('projects', 'Active projects', sum(item.status not in {'Complete', 'Cancelled'} for item in orders), 'Your current projects'), card('quotes', 'My quotations', len(quote_ids), 'Quotes shared with you'), card('products', 'Catalog products', products, 'Browse the furniture catalog')]
        focus = 'Review your latest quotation or project update.'
    return jsonify({'cards': cards, 'focus': focus, 'role': user.role, 'mode': 'api'})
