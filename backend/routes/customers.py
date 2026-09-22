from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Customer
from ..utils import current_user, roles_required

customers_bp = Blueprint('customers', __name__)

FIELDS = ['company', 'contact_name', 'email', 'phone', 'billing_address', 'project_address', 'gstin', 'notes']


def apply_payload(customer, payload):
    for field in FIELDS:
        if field in payload:
            setattr(customer, field, str(payload.get(field, '')).strip())
    if not customer.company or not customer.contact_name:
        raise ValueError('Company and contact name are required.')
    return customer


@customers_bp.get('')
@roles_required('admin', 'sales', 'designer')
def list_customers():
    query = db.select(Customer).order_by(Customer.company); search = request.args.get('q', '').strip(); include_archived = request.args.get('include_archived', '').lower() == 'true' and current_user().role == 'admin'
    if not include_archived: query = query.where(Customer.is_active.is_(True))
    if search:
        like = f'%{search}%'; query = query.where(or_(Customer.company.ilike(like), Customer.contact_name.ilike(like), Customer.email.ilike(like)))
    try: page = max(int(request.args.get('page', 1)), 1); page_size = min(max(int(request.args.get('page_size', 50)), 1), 100)
    except ValueError: return jsonify({'message': 'page and page_size must be valid numbers.'}), 400
    total = db.session.scalar(db.select(db.func.count()).select_from(query.subquery())) or 0; items = db.session.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'pagination': {'page': page, 'page_size': page_size, 'total': total, 'pages': (total + page_size - 1) // page_size}, 'mode': 'api'})


@customers_bp.post('')
@roles_required('admin', 'sales')
def create_customer():
    customer = Customer()
    try:
        apply_payload(customer, request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    db.session.add(customer)
    db.session.commit()
    return jsonify({'item': customer.to_dict(), 'mode': 'api'}), 201


@customers_bp.patch('/<int:customer_id>')
@roles_required('admin', 'sales')
def update_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    try:
        apply_payload(customer, request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    db.session.commit()
    return jsonify({'item': customer.to_dict(), 'mode': 'api'})


@customers_bp.delete('/<int:customer_id>')
@roles_required('admin')
def archive_customer(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    customer.is_active = False
    db.session.commit()
    return jsonify({'item': customer.to_dict(), 'mode': 'api'})
