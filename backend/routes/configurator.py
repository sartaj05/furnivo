import json
from decimal import Decimal, InvalidOperation
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Customer, CustomerPricing, FurnitureConfiguration, Product, ProductVariant, QuotePreset
from ..services.audit import record_audit
from ..utils import current_user, roles_required

configurator_bp = Blueprint('configurator', __name__)
CONFIGURATOR_ROLES = ('admin', 'sales', 'designer')

CONFIGURATION_OPTIONS = {
    'materials': [
        {'value': 'Oak', 'label': 'Oak', 'price_delta': 0},
        {'value': 'Ash', 'label': 'Ash', 'price_delta': 2800},
        {'value': 'Walnut', 'label': 'Walnut', 'price_delta': 6500},
        {'value': 'Engineered wood', 'label': 'Engineered wood', 'price_delta': -1800},
    ],
    'fabrics': [
        {'value': 'Performance fabric', 'label': 'Performance fabric', 'price_delta': 0},
        {'value': 'Sand boucle', 'label': 'Sand boucle', 'price_delta': 3200},
        {'value': 'Velvet', 'label': 'Velvet', 'price_delta': 4200},
        {'value': 'Leather', 'label': 'Leather', 'price_delta': 9800},
    ],
    'colors': [
        {'value': 'Natural', 'label': 'Natural', 'price_delta': 0, 'swatch': '#c7ab83'},
        {'value': 'Sage', 'label': 'Sage', 'price_delta': 900, 'swatch': '#879b87'},
        {'value': 'Terracotta', 'label': 'Terracotta', 'price_delta': 1200, 'swatch': '#bd745b'},
        {'value': 'Charcoal', 'label': 'Charcoal', 'price_delta': 1500, 'swatch': '#454946'},
    ],
    'finishes': [
        {'value': 'Matte', 'label': 'Matte', 'price_delta': 0},
        {'value': 'Natural oil', 'label': 'Natural oil', 'price_delta': 1800},
        {'value': 'High gloss', 'label': 'High gloss', 'price_delta': 2600},
    ],
    'dimension_surcharge_percent': 8,
}


def _option_price(group, value):
    return next((item['price_delta'] for item in CONFIGURATION_OPTIONS.get(group, []) if item['value'] == value), None)


def _positive_dimension(value, label):
    if value in (None, ''):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{label} must be a whole number.')
    if result < 100 or result > 10000:
        raise ValueError(f'{label} must be between 100 and 10000 mm.')
    return result


def _configuration_item(payload):
    product = db.session.get(Product, int(payload.get('product_id'))) if payload.get('product_id') else None
    if not product or not product.is_active:
        raise ValueError('Every configuration item needs an active product.')
    variant = db.session.get(ProductVariant, int(payload.get('variant_id'))) if payload.get('variant_id') else None
    if variant and variant.product_id != product.id:
        raise ValueError('Selected variant does not belong to the product.')
    try:
        quantity = Decimal(str(payload.get('quantity', 1)))
    except (InvalidOperation, ValueError):
        raise ValueError('Quantity must be a valid number.')
    if quantity <= 0 or quantity > 10000:
        raise ValueError('Quantity must be greater than zero and no more than 10000.')

    options = payload.get('options') if isinstance(payload.get('options'), dict) else {}
    selected_options = {}
    option_total = Decimal('0')
    for group, key in (('materials', 'material'), ('fabrics', 'fabric'), ('colors', 'color'), ('finishes', 'finish')):
        value = str(options.get(key, '')).strip()
        if not value:
            continue
        delta = _option_price(group, value)
        if delta is None:
            raise ValueError(f'Unsupported {key} option.')
        selected_options[key] = value
        option_total += Decimal(str(delta))

    dimensions_payload = payload.get('dimensions') if isinstance(payload.get('dimensions'), dict) else {}
    dimensions = {key: _positive_dimension(dimensions_payload.get(key), key.title()) for key in ('width', 'height', 'depth')}
    dimensions = {key: value for key, value in dimensions.items() if value is not None}
    dimension_surcharge = Decimal('0')
    if dimensions:
        defaults = {
            'width': variant.width_mm if variant else None,
            'height': variant.height_mm if variant else None,
            'depth': variant.depth_mm if variant else None,
        }
        if any(defaults.get(key) != value for key, value in dimensions.items()):
            dimension_surcharge = (Decimal(str(product.price or 0)) * Decimal(str(CONFIGURATION_OPTIONS['dimension_surcharge_percent'])) / 100)

    base_price = Decimal(str(product.price or 0)) + Decimal(str(variant.price_delta if variant else 0))
    unit_price = max(base_price + option_total + dimension_surcharge, Decimal('0')).quantize(Decimal('0.01'))
    sku = variant.sku if variant else product.sku
    dimension_label = ' x '.join(str(dimensions[key]) for key in ('width', 'height', 'depth') if dimensions.get(key))
    option_label = ', '.join(value for value in selected_options.values())
    description_parts = [product.name]
    if option_label:
        description_parts.append(option_label)
    if dimension_label:
        description_parts.append(f'{dimension_label} mm')
    return {
        'product_id': product.id,
        'variant_id': variant.id if variant else None,
        'product': product.name,
        'sku': sku,
        'description': ' · '.join(description_parts),
        'quantity': float(quantity),
        'unit': product.unit,
        'unit_price': float(unit_price),
        'line_total': float((quantity * unit_price).quantize(Decimal('0.01'))),
        'options': selected_options,
        'dimensions': dimensions,
        'dimension_surcharge': float(dimension_surcharge),
        'image': product.image,
    }


def next_configuration_number():
    numbers = []
    for value in db.session.scalars(db.select(FurnitureConfiguration.configuration_number)).all():
        try:
            numbers.append(int(str(value).split('-')[-1]))
        except ValueError:
            continue
    return f'CFG-{max(numbers, default=2000) + 1}'


@configurator_bp.get('/options')
@roles_required(*CONFIGURATOR_ROLES)
def get_configuration_options():
    return jsonify({'options': CONFIGURATION_OPTIONS, 'mode': 'api'})


@configurator_bp.get('/configurations')
@roles_required(*CONFIGURATOR_ROLES)
def list_configurations():
    items = db.session.scalars(db.select(FurnitureConfiguration).order_by(FurnitureConfiguration.id.desc())).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@configurator_bp.post('/configurations')
@roles_required(*CONFIGURATOR_ROLES)
def create_configuration():
    payload = request.get_json(silent=True) or {}
    raw_items = payload.get('items') if isinstance(payload.get('items'), list) else []
    if not raw_items:
        return jsonify({'message': 'Add at least one product to the configuration.'}), 400
    try:
        items = [_configuration_item(item) for item in raw_items]
        customer_id = int(payload['customer_id']) if payload.get('customer_id') else None
        if customer_id and not db.session.get(Customer, customer_id):
            raise ValueError('Selected customer was not found.')
        name = str(payload.get('name', '')).strip()
        if not name:
            raise ValueError('Configuration name is required.')
        subtotal = sum((Decimal(str(item['line_total'])) for item in items), Decimal('0')).quantize(Decimal('0.01'))
        item = FurnitureConfiguration(
            configuration_number=next_configuration_number(),
            name=name,
            room=str(payload.get('room', '')).strip(),
            customer_id=customer_id,
            status='Saved',
            items_json=json.dumps(items),
            subtotal=subtotal,
            created_by_id=current_user().id,
        )
        db.session.add(item)
        db.session.commit()
        record_audit(current_user().id, 'Furniture configuration saved', 'configuration', item.id, item.configuration_number)
        db.session.commit()
        return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201
    except (TypeError, ValueError, InvalidOperation) as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 400


@configurator_bp.get('/presets')
@roles_required(*CONFIGURATOR_ROLES)
def list_presets():
    items = db.session.scalars(db.select(QuotePreset).order_by(QuotePreset.name)).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@configurator_bp.post('/presets')
@roles_required(*CONFIGURATOR_ROLES)
def create_preset():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    items = payload.get('items') if isinstance(payload.get('items'), list) else []
    if not name or not items:
        return jsonify({'message': 'Preset name and at least one product are required.'}), 400
    try:
        discount = Decimal(str(payload.get('discount_percent', 0)))
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Preset discount must be valid.'}), 400
    if discount < 0 or discount > 100:
        return jsonify({'message': 'Preset discount must be between 0 and 100.'}), 400
    item = QuotePreset(
        name=name,
        kind=str(payload.get('kind', 'Template')).strip() or 'Template',
        room=str(payload.get('room', '')).strip(),
        description=str(payload.get('description', '')).strip(),
        discount_percent=discount,
        items_json=json.dumps(items),
        created_by_id=current_user().id,
    )
    db.session.add(item)
    db.session.commit()
    record_audit(current_user().id, 'Quotation preset created', 'quote_preset', item.id, item.name)
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'}), 201


@configurator_bp.get('/pricing/<int:customer_id>')
@roles_required(*CONFIGURATOR_ROLES)
def get_customer_pricing(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    item = db.session.scalar(db.select(CustomerPricing).where(CustomerPricing.customer_id == customer.id))
    if not item:
        return jsonify({'item': {'customer_id': customer.id, 'customer': customer.company, 'tier': 'Standard', 'discount_percent': 0}, 'mode': 'api'})
    return jsonify({'item': item.to_dict(), 'mode': 'api'})


@configurator_bp.put('/pricing/<int:customer_id>')
@roles_required('admin', 'sales')
def save_customer_pricing(customer_id):
    customer = db.get_or_404(Customer, customer_id)
    payload = request.get_json(silent=True) or {}
    try:
        discount = Decimal(str(payload.get('discount_percent', 0)))
    except (InvalidOperation, ValueError):
        return jsonify({'message': 'Customer discount must be valid.'}), 400
    if discount < 0 or discount > 100:
        return jsonify({'message': 'Customer discount must be between 0 and 100.'}), 400
    item = db.session.scalar(db.select(CustomerPricing).where(CustomerPricing.customer_id == customer.id))
    if not item:
        item = CustomerPricing(customer_id=customer.id)
        db.session.add(item)
    item.tier = str(payload.get('tier', 'Standard')).strip() or 'Standard'
    item.discount_percent = discount
    db.session.commit()
    record_audit(current_user().id, 'Customer pricing updated', 'customer', customer.id, f'{item.tier} tier / {discount}%')
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
