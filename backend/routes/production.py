from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import BomItem, Order, ProductionJob, QuoteClientAccess
from ..services.audit import record_audit
from ..utils import current_user, roles_required

production_bp = Blueprint('production', __name__)


def next_job_number():
    numbers = []
    for value in db.session.scalars(db.select(ProductionJob.job_number)).all():
        try: numbers.append(int(str(value).split('-')[-1]))
        except ValueError: continue
    return f'JOB-{max(numbers, default=5000) + 1}'


def parse_date(value):
    if not value: return None
    try: return date.fromisoformat(str(value))
    except ValueError: raise ValueError('Production dates must use YYYY-MM-DD format.')


def access_allowed(job):
    if current_user().role != 'client': return True
    return bool(db.session.scalar(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == job.order.quote_id, QuoteClientAccess.user_id == current_user().id)))


@production_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_jobs():
    jobs = db.session.scalars(db.select(ProductionJob).order_by(ProductionJob.id.desc())).unique().all()
    return jsonify({'items': [job.to_dict() for job in jobs if access_allowed(job)], 'mode': 'api'})


@production_bp.post('')
@roles_required('admin', 'sales', 'designer')
def create_job():
    payload = request.get_json(silent=True) or {}
    order = db.session.get(Order, int(payload.get('order_id'))) if payload.get('order_id') else None
    if not order: return jsonify({'message': 'Choose a valid order.'}), 400
    if db.session.scalar(db.select(ProductionJob).where(ProductionJob.order_id == order.id)):
        return jsonify({'message': 'A production job already exists for this order.'}), 409
    try:
        wastage = Decimal(str(payload.get('wastage_percent', 0)))
        job = ProductionJob(order_id=order.id, job_number=next_job_number(), status='Planned', scheduled_start=parse_date(payload.get('scheduled_start')), due_date=parse_date(payload.get('due_date')), assigned_team=str(payload.get('assigned_team', '')).strip(), wastage_percent=wastage, notes=str(payload.get('notes', '')).strip(), created_by_id=current_user().id)
        for row in payload.get('bom_items') or []:
            item_wastage = Decimal(str(row.get('wastage_percent', wastage)))
            job.bom_items.append(BomItem(product_id=row.get('product_id') or None, description=str(row.get('description', '')).strip(), quantity=Decimal(str(row.get('quantity', 1))), unit=str(row.get('unit', 'piece')).strip() or 'piece', wastage_percent=item_wastage, unit_cost=Decimal(str(row.get('unit_cost', 0) or 0)), labor_cost=Decimal(str(row.get('labor_cost', 0) or 0))))
        if not job.bom_items: return jsonify({'message': 'At least one BOM material is required.'}), 400
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Production quantities, wastage, or dates are invalid.'}), 400
    if any(not item.description or item.quantity <= 0 or item.wastage_percent < 0 for item in job.bom_items): return jsonify({'message': 'BOM materials need descriptions, positive quantities, and valid wastage.'}), 400
    db.session.add(job); db.session.commit(); record_audit(current_user().id, 'Production job created', 'production_job', job.id, job.job_number); db.session.commit()
    return jsonify({'item': job.to_dict(), 'mode': 'api'}), 201


@production_bp.patch('/<int:job_id>')
@roles_required('admin', 'sales', 'designer')
def update_job(job_id):
    job = db.get_or_404(ProductionJob, job_id); payload = request.get_json(silent=True) or {}
    if 'status' in payload and payload['status'] not in {'Planned', 'Cutting', 'Assembly', 'Quality check', 'Ready', 'Complete', 'On hold'}: return jsonify({'message': 'Invalid production status.'}), 400
    try:
        for field in ('scheduled_start', 'due_date'):
            if field in payload: setattr(job, field, parse_date(payload[field]))
        for field in ('status', 'assigned_team', 'notes'):
            if field in payload: setattr(job, field, str(payload[field]).strip())
        if 'wastage_percent' in payload: job.wastage_percent = Decimal(str(payload['wastage_percent']))
    except (InvalidOperation, ValueError): return jsonify({'message': 'Production update is invalid.'}), 400
    db.session.commit(); record_audit(current_user().id, 'Production job updated', 'production_job', job.id, job.status); db.session.commit()
    return jsonify({'item': job.to_dict(), 'mode': 'api'})
