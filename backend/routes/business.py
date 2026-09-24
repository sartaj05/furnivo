from collections import defaultdict
from decimal import Decimal
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import BomItem, InventoryItem, Notification, Product, ProductionJob, User
from ..services.audit import record_audit
from ..services.notifications import create_notification, deliver_notification
from ..utils import current_user, roles_required

business_bp = Blueprint('business', __name__)
INTERNAL_ROLES = ('admin', 'sales', 'designer')

AUTOMATION_TEMPLATES = [
    {'event': 'quote_approved', 'label': 'Quote approved', 'title': 'Quotation approved', 'body': '{{quote_number}} for {{customer}} has been approved.', 'channels': ['in_app', 'email', 'whatsapp']},
    {'event': 'deposit_paid', 'label': 'Deposit paid', 'title': 'Deposit payment received', 'body': 'The deposit for {{order_number}} has been received. Production can proceed.', 'channels': ['in_app', 'email', 'whatsapp']},
    {'event': 'production_update', 'label': 'Production update', 'title': 'Production update', 'body': '{{order_number}} is now at the {{status}} stage.', 'channels': ['in_app', 'email', 'whatsapp']},
    {'event': 'delivery_reminder', 'label': 'Delivery reminder', 'title': 'Delivery reminder', 'body': '{{order_number}} is scheduled for delivery on {{delivery_date}}.', 'channels': ['in_app', 'email', 'whatsapp']},
    {'event': 'support_update', 'label': 'Support update', 'title': 'Support request updated', 'body': 'Support request {{ticket_number}} is now {{status}}.', 'channels': ['in_app', 'email', 'whatsapp']},
]
AUTOMATION_RULES = [{'id': index + 1, 'event': item['event'], 'label': item['label'], 'enabled': True, 'actions': [{'type': 'notify', 'channels': item['channels']}, {'type': 'audit'}]} for index, item in enumerate(AUTOMATION_TEMPLATES)]


def _cost_price(product):
    explicit = Decimal(str(product.cost_price or 0)) if product else Decimal('0')
    return explicit if explicit > 0 else Decimal(str(product.price or 0)) * Decimal('0.45') if product else Decimal('0')


def _planning_snapshot():
    inventory = db.session.scalars(db.select(InventoryItem)).all()
    jobs = db.session.scalars(db.select(ProductionJob).order_by(ProductionJob.id.desc())).unique().all()
    inventory_by_product = defaultdict(list)
    for item in inventory:
        inventory_by_product[item.product_id].append(item)
    material_rows = []
    job_rows = []
    for job in jobs:
        job_cost = Decimal('0')
        job_material_cost = Decimal('0')
        job_labor_cost = Decimal('0')
        shortages = []
        for bom in job.bom_items:
            product = bom.product
            planned = Decimal(str(bom.quantity or 0)) * (Decimal('1') + Decimal(str(bom.wastage_percent or 0)) / 100)
            stock = next((item for item in inventory_by_product.get(bom.product_id, []) if not bom.product_id or item.variant_id is None), None)
            available = Decimal(str(stock.available_quantity if stock else 0))
            unit_cost = Decimal(str(bom.unit_cost or 0)) or _cost_price(product)
            material_cost = planned * unit_cost
            labor_cost = Decimal(str(bom.labor_cost or 0)) or material_cost * Decimal('0.18')
            shortage = max(planned - available, Decimal('0'))
            row = {'id': bom.id, 'inventory_id': stock.id if stock else None, 'job_id': job.id, 'job_number': job.job_number, 'order_number': job.order.order_number if job.order else None, 'product_id': bom.product_id, 'product': product.name if product else bom.description, 'description': bom.description, 'unit': bom.unit, 'required_quantity': float(planned), 'available_quantity': float(available), 'reserved_quantity': float(stock.reserved_quantity if stock else 0), 'shortage_quantity': float(shortage), 'unit_cost': float(unit_cost), 'material_cost': float(material_cost), 'labor_cost': float(labor_cost), 'total_cost': float(material_cost + labor_cost), 'supplier': stock.supplier if stock else 'Supplier to assign', 'location': stock.location if stock else ''}
            material_rows.append(row)
            job_material_cost += material_cost; job_labor_cost += labor_cost; job_cost += material_cost + labor_cost
            if shortage > 0: shortages.append(row)
        job_rows.append({'id': job.id, 'job_number': job.job_number, 'order_number': job.order.order_number if job.order else None, 'customer': job.order.customer_name if job.order else None, 'status': job.status, 'due_date': job.due_date.isoformat() if job.due_date else None, 'material_cost': float(job_material_cost), 'labor_cost': float(job_labor_cost), 'estimated_cost': float(job_cost), 'shortage_count': len(shortages)})
    suggestions = {}
    for row in material_rows:
        if row['shortage_quantity'] <= 0: continue
        key = (row['product_id'], row['supplier'])
        item = suggestions.setdefault(key, {'product_id': row['product_id'], 'product': row['product'], 'supplier': row['supplier'], 'quantity': 0, 'unit_cost': row['unit_cost'], 'estimated_total': 0, 'jobs': []})
        item['quantity'] += row['shortage_quantity']; item['estimated_total'] += row['shortage_quantity'] * row['unit_cost']; item['jobs'].append(row['job_number'])
    total_material = sum((Decimal(str(row['material_cost'])) for row in material_rows), Decimal('0')) if material_rows else Decimal('0')
    total_labor = sum((Decimal(str(row['labor_cost'])) for row in material_rows), Decimal('0')) if material_rows else Decimal('0')
    return {'summary': {'jobs': len(jobs), 'materials': len(material_rows), 'shortages': sum(1 for row in material_rows if row['shortage_quantity'] > 0), 'low_stock_items': sum(1 for item in inventory if item.is_low_stock), 'material_cost': float(total_material), 'labor_cost': float(total_labor), 'estimated_cost': float(total_material + total_labor)}, 'jobs': job_rows, 'materials': material_rows, 'purchase_suggestions': list(suggestions.values()), 'inventory': [item.to_dict() for item in inventory]}


@business_bp.get('/planning')
@roles_required(*INTERNAL_ROLES)
def planning():
    return jsonify({'planning': _planning_snapshot(), 'mode': 'api'})


@business_bp.post('/planning/reserve')
@roles_required(*INTERNAL_ROLES)
def reserve_planning_stock():
    snapshot = _planning_snapshot()
    reserved = []
    for row in snapshot['materials']:
        if row['shortage_quantity'] >= row['required_quantity']:
            continue
        item = db.session.get(InventoryItem, row.get('inventory_id')) if row.get('inventory_id') else None
        if not item:
            item = db.session.scalar(db.select(InventoryItem).where(InventoryItem.product_id == row['product_id'], InventoryItem.variant_id.is_(None)))
        if not item: continue
        reserve_now = min(Decimal(str(row['required_quantity'])), Decimal(str(item.available_quantity)))
        item.reserved_quantity += reserve_now
        reserved.append({'product': row['product'], 'quantity': float(reserve_now), 'job_number': row['job_number']})
    db.session.commit()
    record_audit(current_user().id, 'Production material stock reserved', 'planning', '', f'{len(reserved)} material reservations')
    db.session.commit()
    return jsonify({'reserved': reserved, 'planning': _planning_snapshot(), 'mode': 'api'})


@business_bp.get('/automation')
@roles_required(*INTERNAL_ROLES)
def automation_templates():
    return jsonify({'templates': AUTOMATION_TEMPLATES, 'rules': AUTOMATION_RULES, 'mode': 'api'})


@business_bp.get('/automation/rules')
@roles_required('admin', 'sales')
def automation_rules():
    return jsonify({'rules': AUTOMATION_RULES, 'mode': 'api'})


@business_bp.patch('/automation/rules/<event>')
@roles_required('admin')
def update_automation_rule(event):
    rule = next((item for item in AUTOMATION_RULES if item['event'] == event), None)
    if not rule: return jsonify({'message': 'Automation rule not found.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'enabled' in payload: rule['enabled'] = bool(payload['enabled'])
    if isinstance(payload.get('actions'), list) and payload['actions']: rule['actions'] = payload['actions']
    record_audit(current_user().id, 'Automation rule updated', 'automation_rule', event, f"enabled={rule['enabled']}")
    db.session.commit()
    return jsonify({'rule': rule, 'mode': 'api'})


@business_bp.post('/automation/preview')
@roles_required(*INTERNAL_ROLES)
def automation_preview():
    payload = request.get_json(silent=True) or {}
    template = next((item for item in AUTOMATION_TEMPLATES if item['event'] == payload.get('event')), None)
    if not template: return jsonify({'message': 'Choose a valid automation event.'}), 400
    rule = next(item for item in AUTOMATION_RULES if item['event'] == template['event'])
    variables = payload.get('variables') if isinstance(payload.get('variables'), dict) else {}
    body = template['body']
    for key, value in variables.items(): body = body.replace('{{' + key + '}}', str(value))
    return jsonify({'preview': {'event': template['event'], 'title': template['title'], 'body': body, 'channels': template['channels'], 'enabled': rule['enabled'], 'actions': rule['actions']}, 'mode': 'api'})


@business_bp.post('/automation/send')
@roles_required(*INTERNAL_ROLES)
def automation_send():
    payload = request.get_json(silent=True) or {}
    template = next((item for item in AUTOMATION_TEMPLATES if item['event'] == payload.get('event')), None)
    rule = next((item for item in AUTOMATION_RULES if item['event'] == payload.get('event')), None)
    user = db.session.get(User, int(payload.get('user_id'))) if payload.get('user_id') else None
    if not template or not user: return jsonify({'message': 'Automation event and recipient user are required.'}), 400
    if not rule['enabled']: return jsonify({'message': 'This automation rule is disabled.'}), 409
    variables = payload.get('variables') if isinstance(payload.get('variables'), dict) else {}
    body = template['body']
    for key, value in variables.items(): body = body.replace('{{' + key + '}}', str(value))
    notification = create_notification(user.id, template['title'], body, 'automation', payload.get('related_type', ''), payload.get('related_id', ''))
    db.session.commit()
    channel = str(payload.get('channel', 'in_app')).lower()
    delivery = None
    if channel in {'email', 'whatsapp', 'sms'}:
        delivery = deliver_notification(notification, channel, str(payload.get('recipient') or user.email))
    record_audit(current_user().id, 'Automation notification sent', 'notification', notification.id, template['event'])
    db.session.commit()
    return jsonify({'item': notification.to_dict(), 'delivery': delivery.to_dict() if delivery else None, 'mode': 'api'})
