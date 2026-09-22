from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Contract, DeliverySchedule, Invoice, Order, ProductionJob, ProjectSupportTicket, QuoteClientAccess
from ..services.audit import record_audit
from ..utils import current_user, roles_required

portal_bp = Blueprint('portal', __name__)


def client_quote_ids():
    return db.session.scalars(db.select(QuoteClientAccess.quote_id).where(QuoteClientAccess.user_id == current_user().id)).all()


@portal_bp.get('')
@roles_required('client')
def project_portal():
    quote_ids = client_quote_ids()
    orders = db.session.scalars(db.select(Order).where(Order.quote_id.in_(quote_ids or [-1])).order_by(Order.id.desc())).unique().all()
    projects = []
    documents = []
    for order in orders:
        production = db.session.scalar(db.select(ProductionJob).where(ProductionJob.order_id == order.id))
        schedules = db.session.scalars(db.select(DeliverySchedule).where(DeliverySchedule.order_id == order.id).order_by(DeliverySchedule.scheduled_date)).all()
        invoice = db.session.scalar(db.select(Invoice).where(Invoice.order_id == order.id))
        contract = db.session.scalar(db.select(Contract).where(Contract.quote_id == order.quote_id))
        if invoice: documents.append({'type': 'Invoice', 'number': invoice.invoice_number, 'status': invoice.status, 'amount': float(invoice.total or 0)})
        if contract: documents.append({'type': 'Contract', 'number': contract.contract_number, 'status': contract.status, 'id': contract.id})
        projects.append({'order': order.to_dict(), 'production': production.to_dict() if production else None, 'schedules': [schedule.to_dict() for schedule in schedules], 'invoice': invoice.to_dict() if invoice else None, 'contract': contract.to_dict() if contract else None})
    tickets = db.session.scalars(db.select(ProjectSupportTicket).where(ProjectSupportTicket.user_id == current_user().id).order_by(ProjectSupportTicket.id.desc())).all()
    return jsonify({'projects': projects, 'documents': documents, 'support_tickets': [ticket.to_dict() for ticket in tickets], 'mode': 'api'})


@portal_bp.post('/tickets')
@roles_required('client')
def create_ticket():
    payload = request.get_json(silent=True) or {}; order = db.session.get(Order, int(payload.get('order_id'))) if payload.get('order_id') else None
    if not order or order.quote_id not in client_quote_ids(): return jsonify({'message': 'Choose one of your active projects.'}), 403
    subject = str(payload.get('subject', '')).strip(); message = str(payload.get('message', '')).strip()
    if not subject or not message: return jsonify({'message': 'Subject and message are required.'}), 400
    item = ProjectSupportTicket(order_id=order.id, user_id=current_user().id, subject=subject, message=message)
    db.session.add(item); db.session.commit(); record_audit(current_user().id, 'Project support ticket created', 'support_ticket', item.id, item.subject); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@portal_bp.get('/tickets')
@roles_required('admin', 'sales', 'client')
def list_tickets():
    query = db.select(ProjectSupportTicket).order_by(ProjectSupportTicket.id.desc())
    if current_user().role == 'client': query = query.where(ProjectSupportTicket.user_id == current_user().id)
    return jsonify({'items': [item.to_dict() for item in db.session.scalars(query).all()], 'mode': 'api'})


@portal_bp.patch('/tickets/<int:ticket_id>')
@roles_required('admin', 'sales')
def update_ticket(ticket_id):
    item = db.get_or_404(ProjectSupportTicket, ticket_id); payload = request.get_json(silent=True) or {}; status = str(payload.get('status', item.status)).strip()
    if status not in {'Open', 'In progress', 'Resolved'}: return jsonify({'message': 'Invalid support status.'}), 400
    item.status = status; item.response = str(payload.get('response', item.response)).strip(); db.session.commit(); record_audit(current_user().id, 'Project support ticket updated', 'support_ticket', item.id, status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
