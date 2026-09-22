from flask import Blueprint, jsonify
from ..extensions import db
from ..models import Notification
from ..utils import current_user, roles_required

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_notifications():
    items = db.session.scalars(
        db.select(Notification).where(Notification.user_id == current_user().id).order_by(Notification.id.desc()).limit(50)
    ).all()
    return jsonify({'items': [item.to_dict() for item in items], 'mode': 'api'})


@notifications_bp.patch('/<int:notification_id>/read')
@roles_required('admin', 'sales', 'designer', 'client')
def mark_read(notification_id):
    item = db.session.scalar(db.select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user().id))
    if not item:
        return jsonify({'message': 'Notification not found.'}), 404
    item.is_read = True
    db.session.commit()
    return jsonify({'item': item.to_dict(), 'mode': 'api'})
