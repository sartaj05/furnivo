from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Product
from ..utils import roles_required

recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.post('')
@roles_required('admin', 'sales', 'designer', 'client')
def recommend_products():
    payload = request.get_json(silent=True) or {}; room = str(payload.get('room', '')).lower(); material = str(payload.get('material', '')).lower(); color = str(payload.get('color', '')).lower(); budget = float(payload.get('budget', 0) or 0)
    products = db.session.scalars(db.select(Product).where(Product.is_active.is_(True))).all(); results = []
    for product in products:
        text = f'{product.name} {product.category} {product.material} {product.description}'.lower(); score = 0
        if room and room in text: score += 4
        if material and material in text: score += 3
        if color and color in text: score += 2
        if budget and float(product.price or 0) <= budget: score += 2
        if not score: score = 1
        reason = 'Matches your available catalogue and budget.' if score < 4 else f'Good match for {room or "your room"} preferences.'
        results.append({'product': product.to_dict(), 'score': score, 'reason': reason, 'suggested_price': float(product.price or 0)})
    results.sort(key=lambda item: (-item['score'], item['suggested_price']))
    return jsonify({'items': results[:8], 'profile': {'room': room, 'material': material, 'color': color, 'budget': budget}, 'mode': 'api', 'engine': 'Furnivo recommendation engine'})
