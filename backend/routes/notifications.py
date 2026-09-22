from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Notification
from ..services.notifications import deliver_notification
from ..services.audit import record_audit
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


@notifications_bp.post('/<int:notification_id>/deliver')
@roles_required('admin', 'sales', 'designer', 'client')
def deliver(notification_id):
    item = db.session.scalar(db.select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user().id))
    if not item:
        return jsonify({'message': 'Notification not found.'}), 404
    payload = request.get_json(silent=True) or {}
    channel = str(payload.get('channel', '')).strip().lower()
    recipient = str(payload.get('recipient') or (current_user().email if channel == 'email' else '')).strip()
    if channel not in {'email', 'whatsapp'} or not recipient:
        return jsonify({'message': 'Choose email or WhatsApp and provide a recipient.'}), 400
    delivery = deliver_notification(item, channel, recipient)
    record_audit(current_user().id, 'Notification delivery requested', 'notification', item.id, f'{channel} to {recipient}'); db.session.commit()
    return jsonify({'item': delivery.to_dict(), 'mode': 'api'})
