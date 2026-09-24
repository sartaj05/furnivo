import csv
import io
import json
from flask import Blueprint, current_app, jsonify, request
from ..extensions import db
from ..models import BackgroundJob, Customer, Product
from ..services.audit import record_audit
from ..services.jobs import enqueue_job, worker_status
from ..utils import current_user, roles_required

data_admin_bp = Blueprint('data_admin', __name__)


@data_admin_bp.get('/jobs')
@roles_required('admin')
def list_jobs():
    return jsonify({'items': [item.to_dict() for item in db.session.scalars(db.select(BackgroundJob).order_by(BackgroundJob.id.desc()).limit(50)).all()], 'mode': 'api'})


@data_admin_bp.get('/worker-status')
@roles_required('admin')
def worker_health():
    return jsonify({'worker': worker_status(current_app.config), 'mode': 'api'})


@data_admin_bp.post('/jobs')
@roles_required('admin')
def create_job():
    payload = request.get_json(silent=True) or {}; job_type = str(payload.get('job_type', '')).strip()
    if job_type not in {'catalog-reindex', 'report-refresh'}: return jsonify({'message': 'Unsupported background job type.'}), 400
    item = BackgroundJob(job_type=job_type, payload_json=json.dumps(payload), created_by_id=current_user().id); db.session.add(item); db.session.commit(); enqueue_job(current_app._get_current_object(), item.id)
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 202


@data_admin_bp.post('/jobs/<int:job_id>/retry')
@roles_required('admin')
def retry_job(job_id):
    item = db.session.get(BackgroundJob, job_id)
    if not item: return jsonify({'message': 'Background job not found.'}), 404
    if item.status != 'Failed': return jsonify({'message': 'Only failed jobs can be retried.'}), 400
    item.status = 'Queued'; item.error = ''; item.result_json = '{}'; db.session.commit()
    enqueue_job(current_app._get_current_object(), item.id)
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 202


def parse_csv_file():
    uploaded = request.files.get('file')
    if not uploaded: raise ValueError('CSV file is required.')
    return csv.DictReader(io.StringIO(uploaded.stream.read().decode('utf-8-sig')))


@data_admin_bp.post('/products/import')
@roles_required('admin')
def import_products():
    try: rows = parse_csv_file(); created = updated = errors = 0
    except (UnicodeDecodeError, ValueError) as exc: return jsonify({'message': str(exc)}), 400
    for row in rows:
        try:
            sku = str(row.get('sku', '')).strip().upper(); name = str(row.get('name', '')).strip(); category = str(row.get('category', '')).strip()
            if not sku or not name or not category: raise ValueError('sku, name and category are required')
            item = db.session.scalar(db.select(Product).where(Product.sku == sku))
            if item: item.name = name; item.category = category; updated += 1
            else: item = Product(sku=sku, name=name, category=category); db.session.add(item); created += 1
            item.price = float(row.get('price') or 0); item.unit = str(row.get('unit', 'piece')).strip() or 'piece'; item.material = str(row.get('material', '')).strip(); item.description = str(row.get('description', '')).strip(); item.is_active = str(row.get('is_active', 'true')).lower() not in {'false', '0', 'no'}
        except (ValueError, TypeError): errors += 1
    db.session.commit(); record_audit(current_user().id, 'Products imported', 'data_import', '', f'created={created}, updated={updated}, errors={errors}'); db.session.commit()
    return jsonify({'created': created, 'updated': updated, 'errors': errors, 'mode': 'api'})


@data_admin_bp.post('/customers/import')
@roles_required('admin')
def import_customers():
    try: rows = parse_csv_file(); created = updated = errors = 0
    except (UnicodeDecodeError, ValueError) as exc: return jsonify({'message': str(exc)}), 400
    for row in rows:
        try:
            company = str(row.get('company', '')).strip(); contact = str(row.get('contact_name', '')).strip()
            if not company or not contact: raise ValueError('company and contact_name are required')
            item = db.session.scalar(db.select(Customer).where(Customer.company == company))
            if not item: item = Customer(company=company, contact_name=contact); db.session.add(item); created += 1
            else: updated += 1
            for field in ['contact_name', 'email', 'phone', 'billing_address', 'project_address', 'gstin', 'notes']:
                if field in row: setattr(item, field, str(row.get(field, '')).strip())
        except (ValueError, TypeError): errors += 1
    db.session.commit(); record_audit(current_user().id, 'Customers imported', 'data_import', '', f'created={created}, updated={updated}, errors={errors}'); db.session.commit()
    return jsonify({'created': created, 'updated': updated, 'errors': errors, 'mode': 'api'})
