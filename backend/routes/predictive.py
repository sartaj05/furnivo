from collections import defaultdict
from datetime import date
from flask import Blueprint, jsonify
from ..extensions import db
from ..models import InventoryItem, PurchaseOrder, QualityInspection
from ..utils import roles_required

predictive_bp = Blueprint('predictive', __name__)


@predictive_bp.get('')
@roles_required('admin', 'sales', 'designer')
def predictive_analytics():
    purchase_orders = db.session.scalars(db.select(PurchaseOrder)).all()
    supplier_stats = defaultdict(lambda: {'supplier': '', 'orders': 0, 'average_lead_days': 0, 'late_orders': 0})
    for order in purchase_orders:
        if not order.expected_date: continue
        row = supplier_stats[order.supplier_id]; row['supplier'] = order.supplier.name if order.supplier else 'Unknown'; row['orders'] += 1
        end = order.actual_delivery_date or date.today(); row['average_lead_days'] += max((end - order.order_date).days, 0)
        if order.actual_delivery_date and order.actual_delivery_date > order.expected_date: row['late_orders'] += 1
    lead_times = []
    for row in supplier_stats.values():
        row['average_lead_days'] = round(row['average_lead_days'] / row['orders'], 1) if row['orders'] else 0
        row['late_rate'] = round(row['late_orders'] / row['orders'] * 100, 1) if row['orders'] else 0
        lead_times.append(row)
    inspections = db.session.scalars(db.select(QualityInspection)).all()
    defects = sum(item.status in {'Failed', 'Rework'} for item in inspections)
    recommendations = []
    for item in db.session.scalars(db.select(InventoryItem)).all():
        available = float(item.available_quantity); reorder = float(item.reorder_level or 0)
        if available <= reorder:
            recommendations.append({'inventory_id': item.id, 'product': item.product.name if item.product else 'Material', 'available_quantity': available, 'reorder_level': reorder, 'suggested_order_quantity': max(reorder * 2 - available, 1), 'risk': 'Critical' if available <= reorder * 0.5 else 'Watch', 'supplier': item.supplier})
    return jsonify({'supplier_lead_times': lead_times, 'quality': {'inspection_count': len(inspections), 'defect_rate': round(defects / len(inspections) * 100, 1) if inspections else 0, 'rework_cost': round(sum(float(item.rework_cost or 0) for item in inspections), 2)}, 'purchase_recommendations': recommendations, 'mode': 'api'})
