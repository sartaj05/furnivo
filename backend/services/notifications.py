from ..extensions import db
from ..models import Notification, QuoteClientAccess, User


def create_notification(user_id, title, body, notification_type='info', related_type='', related_id=''):
    if not user_id:
        return None
    item = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        related_type=related_type,
        related_id=str(related_id or ''),
    )
    db.session.add(item)
    return item


def notify_roles(roles, title, body, notification_type='info', exclude_user_id=None, related_type='', related_id=''):
    users = db.session.scalars(db.select(User).where(User.role.in_(roles), User.is_active.is_(True))).all()
    return [create_notification(user.id, title, body, notification_type, related_type, related_id) for user in users if user.id != exclude_user_id]


def notify_quote_client(quote, title, body, notification_type='info'):
    accesses = db.session.scalars(db.select(QuoteClientAccess).where(QuoteClientAccess.quote_id == quote.id)).all()
    return [create_notification(access.user_id, title, body, notification_type, 'quote', quote.id) for access in accesses]
