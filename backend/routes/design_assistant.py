import json
import os
import urllib.request
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Product
from ..utils import roles_required

design_bp = Blueprint('design_assistant', __name__)


def fallback_brief(payload, products):
    room = str(payload.get('room', 'living room')).strip(); style = str(payload.get('style', 'warm modern')).strip(); color = str(payload.get('color', 'neutral')).strip(); budget = float(payload.get('budget', 0) or 0)
    ranked = sorted(products, key=lambda item: (0 if budget and float(item.price or 0) > budget else 1, -float(item.price or 0)))[:6]
    return {'title': f'{style.title()} {room.title()} concept', 'layout': [f'Anchor the room with a primary seating zone.', f'Keep a clear circulation path around the {room}.', f'Layer {color} accents through textiles, lighting, and artwork.'], 'moodboard': [{'label': 'Palette', 'value': color}, {'label': 'Style', 'value': style}, {'label': 'Lighting', 'value': 'Warm layered light'}], 'recommendations': [{'product': item.to_dict(), 'reason': f'Fits the {style} direction and requested budget.' if not budget or float(item.price or 0) <= budget else 'Alternative to review above the current budget.'} for item in ranked], 'provider': 'demo-fallback'}


def optional_openai_brief(payload):
    key = os.getenv('OPENAI_API_KEY', '')
    if not key: return None
    prompt = f"Create a concise furniture interior design brief. Room: {payload.get('room', '')}; style: {payload.get('style', '')}; material: {payload.get('material', '')}; color: {payload.get('color', '')}; budget: {payload.get('budget', '')}. Return JSON with title, layout array, moodboard array, and recommendations array."
    content = [{'type': 'input_text', 'text': prompt}]
    if payload.get('image_url'): content.append({'type': 'input_image', 'image_url': payload['image_url']})
    body = json.dumps({'model': os.getenv('OPENAI_DESIGN_MODEL', 'gpt-4.1-mini'), 'input': [{'role': 'user', 'content': content}], 'text': {'format': {'type': 'json_object'}}}).encode()
    req = urllib.request.Request('https://api.openai.com/v1/responses', data=body, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'}, method='POST')
    with urllib.request.urlopen(req, timeout=20) as response: result = json.loads(response.read().decode() or '{}')
    raw = result.get('output_text') or ''
    return {**json.loads(raw), 'provider': 'openai'} if raw else None


@design_bp.post('')
@roles_required('admin', 'sales', 'designer', 'client')
def create_design_brief():
    payload = request.get_json(silent=True) or {}; products = db.session.scalars(db.select(Product).where(Product.is_active.is_(True))).all()
    try: brief = optional_openai_brief(payload)
    except Exception: brief = None
    return jsonify({'brief': brief or fallback_brief(payload, products), 'mode': 'api', 'live_provider_configured': bool(os.getenv('OPENAI_API_KEY'))})
