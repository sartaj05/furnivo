import json
import time
from concurrent.futures import ThreadPoolExecutor
from ..extensions import db
from ..models import BackgroundJob, Invoice, Order, Product

executor = ThreadPoolExecutor(max_workers=2)


def worker_status(config):
    mode = str(config.get('BACKGROUND_JOB_MODE', 'thread')).lower()
    return {
        'mode': mode if mode in {'thread', 'inline'} else 'thread',
        'provider': 'local-thread-pool' if mode == 'thread' else 'inline',
        'capacity': 2 if mode == 'thread' else 1,
        'retryable': True,
    }


def execute_job(app, job_id):
    with app.app_context():
        job = db.session.get(BackgroundJob, job_id)
        if not job: return
        try:
            job.status = 'Running'; db.session.commit(); time.sleep(0.05)
            if job.job_type == 'catalog-reindex': result = {'indexed_products': db.session.scalar(db.select(db.func.count()).select_from(Product)) or 0}
            elif job.job_type == 'report-refresh': result = {'orders': db.session.scalar(db.select(db.func.count()).select_from(Order)) or 0, 'invoices': db.session.scalar(db.select(db.func.count()).select_from(Invoice)) or 0}
            else: raise ValueError('Unsupported background job type.')
            job.status = 'Complete'; job.result_json = json.dumps(result); db.session.commit()
        except Exception as exc:
            job.status = 'Failed'; job.error = str(exc); db.session.commit()


def enqueue_job(app, job_id):
    if str(app.config.get('BACKGROUND_JOB_MODE', 'thread')).lower() == 'inline':
        execute_job(app, job_id)
        return
    executor.submit(execute_job, app, job_id)
