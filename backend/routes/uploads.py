from pathlib import Path
from flask import Blueprint, current_app, jsonify, request
from ..extensions import db
from ..models import MediaAsset
from ..services.storage import delete_asset, save_asset, save_product_image
from ..utils import current_user, roles_required

uploads_bp = Blueprint('uploads', __name__)


def register_asset(result, entity_type='unlinked', entity_id=''):
    item = MediaAsset(provider=result.get('provider', 'local'), public_id=result.get('public_id', ''), url=result['url'], resource_type=result.get('resource_type', 'image'), folder=result.get('folder', ''), entity_type=str(entity_type or 'unlinked'), entity_id=str(entity_id or ''), original_filename=result.get('original_filename', ''), bytes=result.get('bytes', 0), uploaded_by_id=current_user().id)
    db.session.add(item); db.session.commit()
    return item


@uploads_bp.post('/product-image')
@roles_required('admin')
def upload_product_image():
    try:
        result = save_product_image(request.files.get('file'))
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    asset = register_asset(result, 'product', request.form.get('product_id', ''))
    result['asset_id'] = asset.id
    return jsonify({'item': result, 'mode': 'api'}), 201


@uploads_bp.post('/field-proof')
@roles_required('admin', 'sales', 'designer')
def upload_field_proof():
    try:
        result = save_asset(request.files.get('file'), folder='furnivo/field-proofs')
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    asset = register_asset(result, 'field_visit', request.form.get('visit_id', ''))
    result['asset_id'] = asset.id
    return jsonify({'item': result, 'mode': 'api'}), 201


@uploads_bp.post('/design-room')
@roles_required('admin', 'sales', 'designer', 'client')
def upload_design_room():
    try:
        result = save_asset(request.files.get('file'), folder='furnivo/design-rooms')
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    asset = register_asset(result, 'design_room', request.form.get('brief_id', ''))
    result['asset_id'] = asset.id; result['entity_type'] = asset.entity_type
    return jsonify({'item': result, 'mode': 'api'}), 201


@uploads_bp.post('/production-task')
@roles_required('admin', 'sales', 'designer')
def upload_production_task_photo():
    try:
        result = save_asset(request.files.get('file'), folder='furnivo/production-tasks')
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    asset = register_asset(result, 'production_task', request.form.get('task_id', ''))
    result['asset_id'] = asset.id; result['entity_type'] = asset.entity_type; result['entity_id'] = asset.entity_id
    return jsonify({'item': result, 'mode': 'api'}), 201


@uploads_bp.post('/quality-inspection')
@roles_required('admin', 'sales', 'designer')
def upload_quality_inspection_photo():
    try:
        result = save_asset(request.files.get('file'), folder='furnivo/quality-inspections')
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    asset = register_asset(result, 'quality_inspection', request.form.get('inspection_id', ''))
    result['asset_id'] = asset.id; result['entity_type'] = asset.entity_type; result['entity_id'] = asset.entity_id
    return jsonify({'item': result, 'mode': 'api'}), 201


@uploads_bp.get('/assets')
@roles_required('admin')
def list_assets():
    items = db.session.scalars(db.select(MediaAsset).where(MediaAsset.is_active.is_(True)).order_by(MediaAsset.id.desc()).limit(200)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@uploads_bp.delete('/assets/<int:asset_id>')
@roles_required('admin')
def delete_registered_asset(asset_id):
    item = db.get_or_404(MediaAsset, asset_id)
    if item.provider == 'cloudinary':
        delete_asset(item.public_id, item.resource_type)
    elif item.url.startswith('/uploads/'):
        filename = item.url.rsplit('/', 1)[-1]
        path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        if path.exists(): path.unlink()
    item.is_active = False; db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
