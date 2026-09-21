from flask import Blueprint, jsonify, request
from ..services.storage import save_product_image
from ..utils import roles_required

uploads_bp = Blueprint('uploads', __name__)


@uploads_bp.post('/product-image')
@roles_required('admin')
def upload_product_image():
    try:
        result = save_product_image(request.files.get('file'))
    except ValueError as exc:
        return jsonify({'message': str(exc)}), 400
    return jsonify({'item': result, 'mode': 'api'}), 201
