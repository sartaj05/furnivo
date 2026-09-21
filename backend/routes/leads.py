from datetime import date
from decimal import Decimal
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Lead, LeadNote, LeadTask, User
from ..utils import current_user, roles_required

leads_bp = Blueprint('leads', __name__)
STAGES = {'New', 'Qualified', 'Proposal', 'Won', 'Lost'}


@leads_bp.get('')
@roles_required('admin', 'sales')
def list_leads():
    items = db.session.scalars(db.select(Lead).order_by(Lead.updated_at.desc())).unique().all()
    team = db.session.scalars(db.select(User).where(User.role.in_(['admin', 'sales']), User.is_active.is_(True)).order_by(User.name)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'team': [member.public_dict() for member in team], 'mode': 'api'})


@leads_bp.post('')
@roles_required('admin', 'sales')
def create_lead():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    if not name:
        return jsonify({'message': 'Lead name is required.'}), 400
    lead = Lead(
        name=name,
        company=str(payload.get('company', '')).strip(),
        email=str(payload.get('email', '')).strip(),
        phone=str(payload.get('phone', '')).strip(),
        source=str(payload.get('source', 'Website')).strip(),
        stage=str(payload.get('stage', 'New')).strip(),
        value=Decimal(str(payload.get('value', 0) or 0)),
        owner_id=payload.get('owner_id') or current_user().id,
    )
    db.session.add(lead)
    db.session.commit()
    return jsonify({'item': lead.to_dict(), 'mode': 'api'}), 201


@leads_bp.patch('/<int:lead_id>')
@roles_required('admin', 'sales')
def update_lead(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    payload = request.get_json(silent=True) or {}
    if 'stage' in payload:
        if payload['stage'] not in STAGES:
            return jsonify({'message': 'Invalid lead stage.'}), 400
        lead.stage = payload['stage']
    if 'owner_id' in payload:
        lead.owner_id = int(payload['owner_id']) if payload['owner_id'] else None
    for field in ['name', 'company', 'email', 'phone', 'source']:
        if field in payload:
            setattr(lead, field, str(payload[field]).strip())
    if 'value' in payload:
        lead.value = Decimal(str(payload['value'] or 0))
    db.session.commit()
    return jsonify({'item': lead.to_dict(), 'mode': 'api'})


@leads_bp.post('/<int:lead_id>/notes')
@roles_required('admin', 'sales')
def add_note(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    body = str((request.get_json(silent=True) or {}).get('body', '')).strip()
    if not body:
        return jsonify({'message': 'Note cannot be empty.'}), 400
    note = LeadNote(lead=lead, author_id=current_user().id, body=body)
    db.session.add(note)
    db.session.commit()
    return jsonify({'item': note.to_dict(), 'lead': lead.to_dict(), 'mode': 'api'}), 201


@leads_bp.post('/<int:lead_id>/tasks')
@roles_required('admin', 'sales')
def add_task(lead_id):
    lead = db.get_or_404(Lead, lead_id)
    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title', '')).strip()
    if not title:
        return jsonify({'message': 'Task title is required.'}), 400
    due = date.fromisoformat(payload['due_date']) if payload.get('due_date') else None
    task = LeadTask(lead=lead, title=title, due_date=due, assigned_to_id=payload.get('assigned_to_id') or lead.owner_id)
    db.session.add(task)
    db.session.commit()
    return jsonify({'item': task.to_dict(), 'lead': lead.to_dict(), 'mode': 'api'}), 201


@leads_bp.patch('/<int:lead_id>/tasks/<int:task_id>')
@roles_required('admin', 'sales')
def update_task(lead_id, task_id):
    task = db.session.scalar(db.select(LeadTask).where(LeadTask.id == task_id, LeadTask.lead_id == lead_id))
    if not task:
        return jsonify({'message': 'Task not found.'}), 404
    payload = request.get_json(silent=True) or {}
    if 'is_done' in payload:
        task.is_done = bool(payload['is_done'])
    if 'title' in payload:
        task.title = str(payload['title']).strip()
    if 'due_date' in payload:
        task.due_date = date.fromisoformat(payload['due_date']) if payload['due_date'] else None
    db.session.commit()
    return jsonify({'item': task.to_dict(), 'mode': 'api'})
