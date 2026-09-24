import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import BomItem, Order, ProductionJob, ProductionTask, QualityInspection, QuoteClientAccess, utcnow
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


def parse_datetime(value):
    if not value: return None
    try: return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError: raise ValueError('Task dates must use ISO date-time format.')


def task_conflicts(task, tasks=None):
    tasks = tasks if tasks is not None else db.session.scalars(db.select(ProductionTask)).all()
    if not task.planned_start or not task.planned_end: return []
    conflicts = []
    for other in tasks:
        if other.id == task.id or not other.planned_start or not other.planned_end: continue
        shared_resource = (task.assigned_worker and task.assigned_worker == other.assigned_worker) or (task.machine and task.machine == other.machine)
        overlaps = task.planned_start < other.planned_end and task.planned_end > other.planned_start
        if shared_resource and overlaps:
            conflicts.append({'task_id': other.id, 'task_name': other.name, 'resource': 'worker' if task.assigned_worker == other.assigned_worker else 'machine'})
    return conflicts


def schedule_conflicts(tasks):
    return [{'task_id': task.id, 'task_name': task.name, 'conflicts': task_conflicts(task, tasks)} for task in tasks if task_conflicts(task, tasks)]


@production_bp.get('/schedule')
@roles_required('admin', 'sales', 'designer')
def list_production_schedule():
    tasks = db.session.scalars(db.select(ProductionTask).order_by(ProductionTask.planned_start, ProductionTask.id)).all()
    return jsonify({'items': [task.to_dict() for task in tasks], 'conflicts': schedule_conflicts(tasks), 'mode': 'api'})


@production_bp.post('/schedule')
@roles_required('admin', 'sales', 'designer')
def create_production_task():
    payload = request.get_json(silent=True) or {}; job = db.session.get(ProductionJob, payload.get('production_job_id')) if payload.get('production_job_id') else None
    name = str(payload.get('name', '')).strip()
    if not job or not name: return jsonify({'message': 'Production job and task name are required.'}), 400
    try:
        task = ProductionTask(production_job_id=job.id, name=name, stage=str(payload.get('stage', 'Assembly')).strip(), assigned_worker=str(payload.get('assigned_worker', '')).strip(), machine=str(payload.get('machine', '')).strip(), dependency_id=payload.get('dependency_id') or None, planned_start=parse_datetime(payload.get('planned_start')), planned_end=parse_datetime(payload.get('planned_end')), actual_minutes=int(payload.get('actual_minutes', 0) or 0), status=str(payload.get('status', 'Planned')).strip())
    except (TypeError, ValueError): return jsonify({'message': 'Task schedule values are invalid.'}), 400
    if task.actual_minutes < 0: return jsonify({'message': 'Actual minutes cannot be negative.'}), 400
    db.session.add(task); db.session.commit(); record_audit(current_user().id, 'Production task scheduled', 'production_task', task.id, task.name); db.session.commit()
    return jsonify({'item': task.to_dict(), 'mode': 'api'}), 201


@production_bp.patch('/schedule/<int:task_id>')
@roles_required('admin', 'sales', 'designer')
def update_production_task(task_id):
    task = db.get_or_404(ProductionTask, task_id); payload = request.get_json(silent=True) or {}
    for field in ('name', 'stage', 'assigned_worker', 'machine', 'status'):
        if field in payload: setattr(task, field, str(payload[field]).strip())
    if 'dependency_id' in payload:
        dependency_id = payload['dependency_id'] or None
        if dependency_id is not None and int(dependency_id) == task.id:
            return jsonify({'message': 'A task cannot depend on itself.'}), 400
        task.dependency_id = dependency_id
    if 'actual_minutes' in payload: task.actual_minutes = max(int(payload['actual_minutes'] or 0), 0)
    try:
        if 'planned_start' in payload: task.planned_start = parse_datetime(payload['planned_start'])
        if 'planned_end' in payload: task.planned_end = parse_datetime(payload['planned_end'])
    except ValueError as exc: return jsonify({'message': str(exc)}), 400
    if task.planned_start and task.planned_end and task.planned_end <= task.planned_start:
        return jsonify({'message': 'Task end must be after task start.'}), 400
    if task.dependency_id:
        dependency = db.session.get(ProductionTask, task.dependency_id)
        if dependency and dependency.production_job_id != task.production_job_id:
            return jsonify({'message': 'Dependencies must belong to the same production job.'}), 400
        seen = {task.id}; cursor = dependency
        while cursor:
            if cursor.id in seen: return jsonify({'message': 'Task dependencies cannot contain a cycle.'}), 400
            seen.add(cursor.id); cursor = cursor.dependency
    conflicts = task_conflicts(task)
    db.session.commit(); record_audit(current_user().id, 'Production task updated', 'production_task', task.id, task.status); db.session.commit()
    return jsonify({'item': task.to_dict(), 'conflicts': conflicts, 'mode': 'api'})


@production_bp.get('/capacity')
@roles_required('admin', 'sales', 'designer')
def production_capacity():
    tasks = db.session.scalars(db.select(ProductionTask)).all(); workers = {}; machines = {}
    for task in tasks:
        if task.assigned_worker: workers[task.assigned_worker] = workers.get(task.assigned_worker, 0) + max(task.actual_minutes, 0)
        if task.machine: machines[task.machine] = machines.get(task.machine, 0) + max(task.actual_minutes, 0)
    now = utcnow(); alert_count = 0
    for task in tasks:
        if task.planned_end and task.status not in {'Complete', 'Cancelled'}:
            planned_end = task.planned_end if task.planned_end.tzinfo else task.planned_end.replace(tzinfo=timezone.utc)
            alert_count += planned_end < now
    return jsonify({'capacity': {'planned_tasks': len(tasks), 'open_tasks': sum(task.status not in {'Complete', 'Cancelled'} for task in tasks), 'worker_minutes': workers, 'machine_minutes': machines, 'alert_count': alert_count}, 'mode': 'api'})


@production_bp.get('/<int:job_id>/inspections')
@roles_required('admin', 'sales', 'designer', 'client')
def list_inspections(job_id):
    job = db.get_or_404(ProductionJob, job_id)
    if not access_allowed(job): return jsonify({'message': 'You do not have access to this production job.'}), 403
    return jsonify({'items': [item.to_dict() for item in job.inspections], 'mode': 'api'})


@production_bp.post('/<int:job_id>/inspections')
@roles_required('admin', 'sales', 'designer')
def create_inspection(job_id):
    job = db.get_or_404(ProductionJob, job_id); payload = request.get_json(silent=True) or {}; status = str(payload.get('status', 'Pending')).strip()
    if status not in {'Pending', 'Passed', 'Failed', 'Rework'}: return jsonify({'message': 'Invalid inspection status.'}), 400
    checklist = payload.get('checklist') if isinstance(payload.get('checklist'), list) else []; defects = payload.get('defects') if isinstance(payload.get('defects'), list) else []
    try: rework_cost = Decimal(str(payload.get('rework_cost', 0) or 0))
    except InvalidOperation: return jsonify({'message': 'Rework cost must be a valid amount.'}), 400
    if rework_cost < 0: return jsonify({'message': 'Rework cost cannot be negative.'}), 400
    item = QualityInspection(production_job_id=job.id, inspector_id=current_user().id, status=status, checklist_json=json.dumps(checklist), defects_json=json.dumps(defects), photo_url=str(payload.get('photo_url', '')).strip(), notes=str(payload.get('notes', '')).strip(), rework_cost=rework_cost, approved_at=utcnow() if status == 'Passed' else None)
    db.session.add(item); job.status = 'Ready' if status == 'Passed' else 'Quality check' if status in {'Pending', 'Failed'} else 'On hold'; db.session.commit(); record_audit(current_user().id, 'Quality inspection recorded', 'production_job', job.id, status); db.session.commit()
    return jsonify({'item': item.to_dict(), 'job': job.to_dict(), 'mode': 'api'}), 201
