from ..extensions import db
import json
import os
import smtplib
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from ..models import Notification, NotificationDelivery, QuoteClientAccess, User


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


def deliver_notification(notification, channel, recipient):
    delivery = NotificationDelivery(notification_id=notification.id, channel=channel, recipient=recipient, status='queued')
    db.session.add(delivery)
    db.session.flush()
    try:
        if channel == 'email':
            host = os.getenv('SMTP_HOST', '')
            if not host:
                raise RuntimeError('SMTP_HOST is not configured.')
            message = EmailMessage()
            message['Subject'] = notification.title
            message['From'] = os.getenv('NOTIFICATION_FROM_EMAIL', 'notifications@furnivo.local')
            message['To'] = recipient
            message.set_content(notification.body)
            port = int(os.getenv('SMTP_PORT', '587'))
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                if os.getenv('SMTP_TLS', 'true').lower() == 'true':
                    smtp.starttls()
                if os.getenv('SMTP_USERNAME'):
                    smtp.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD', ''))
                smtp.send_message(message)
        elif channel == 'whatsapp':
            webhook = os.getenv('WHATSAPP_WEBHOOK_URL', '')
            if not webhook:
                raise RuntimeError('WHATSAPP_WEBHOOK_URL is not configured.')
            payload = json.dumps({'to': recipient, 'title': notification.title, 'body': notification.body}).encode()
            request = urllib.request.Request(webhook, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status >= 300:
                    raise RuntimeError(f'WhatsApp provider returned HTTP {response.status}.')
        else:
            raise RuntimeError('Unsupported notification channel.')
        delivery.status = 'sent'
    except Exception as exc:
        delivery.status = 'pending_configuration' if 'not configured' in str(exc) else 'failed'
        delivery.error = str(exc)
    delivery.attempted_at = datetime.now(timezone.utc)
    db.session.commit()
    return delivery
