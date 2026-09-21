from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Customer
from ..utils import roles_required

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
@roles_required('admin', 'sales')
def list_customers():
    items = db.session.scalars(db.select(Customer).where(Customer.is_active.is_(True)).order_by(Customer.company)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


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
