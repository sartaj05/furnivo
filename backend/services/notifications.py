from ..extensions import db
import json
import os
import smtplib
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from sqlalchemy import or_
from ..models import Notification, NotificationDelivery, QuoteClientAccess, User


def notification_provider_status():
    email = bool(os.getenv('NOTIFICATION_EMAIL_URL') or os.getenv('SMTP_HOST'))
    whatsapp = bool(os.getenv('WHATSAPP_WEBHOOK_URL'))
    sms = bool(os.getenv('SMS_WEBHOOK_URL'))
    return {'channels': {'in_app': {'configured': True, 'provider': 'Furnivo'}, 'email': {'configured': email, 'provider': 'HTTP provider or SMTP'}, 'whatsapp': {'configured': whatsapp, 'provider': 'Webhook'}, 'sms': {'configured': sms, 'provider': 'Webhook'}}, 'retry_policy': {'max_attempts': 4, 'backoff_minutes': [5, 10, 20, 40]}, 'mode': 'api'}


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


def deliver_notification(notification, channel, recipient, existing_delivery=None):
    delivery = existing_delivery or NotificationDelivery(notification_id=notification.id, channel=channel, recipient=recipient, status='queued')
    if existing_delivery is None:
        db.session.add(delivery)
    db.session.flush()
    delivery.attempt_count += 1
    delivery.status = 'sending'
    delivery.error = ''
    try:
        if channel == 'email':
            provider_url = os.getenv('NOTIFICATION_EMAIL_URL', '')
            if provider_url:
                payload = json.dumps({'to': recipient, 'subject': notification.title, 'text': notification.body, 'idempotency_key': f'notification-delivery-{delivery.id}'}).encode()
                headers = {'Content-Type': 'application/json'}
                if os.getenv('NOTIFICATION_EMAIL_TOKEN'): headers['Authorization'] = f"Bearer {os.getenv('NOTIFICATION_EMAIL_TOKEN')}"
                provider_request = urllib.request.Request(provider_url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(provider_request, timeout=10) as response:
                    if response.status >= 300: raise RuntimeError(f'Email provider returned HTTP {response.status}.')
                    try: provider_result = json.loads(response.read().decode() or '{}')
                    except (TypeError, ValueError): provider_result = {}
                    delivery.provider_message_id = str(provider_result.get('id') or provider_result.get('message_id') or '')
            else:
                host = os.getenv('SMTP_HOST', '')
                if not host: raise RuntimeError('NOTIFICATION_EMAIL_URL is not configured.')
                message = EmailMessage(); message['Subject'] = notification.title; message['From'] = os.getenv('NOTIFICATION_FROM_EMAIL', 'notifications@furnivo.local'); message['To'] = recipient; message.set_content(notification.body)
                port = int(os.getenv('SMTP_PORT', '587'))
                with smtplib.SMTP(host, port, timeout=10) as smtp:
                    if os.getenv('SMTP_TLS', 'true').lower() == 'true': smtp.starttls()
                    if os.getenv('SMTP_USERNAME'): smtp.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD', ''))
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
        elif channel == 'sms':
            webhook = os.getenv('SMS_WEBHOOK_URL', '')
            if not webhook:
                raise RuntimeError('SMS_WEBHOOK_URL is not configured.')
            payload = json.dumps({'to': recipient, 'message': notification.body, 'idempotency_key': f'notification-delivery-{delivery.id}'}).encode()
            provider_request = urllib.request.Request(webhook, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(provider_request, timeout=10) as response:
                if response.status >= 300:
                    raise RuntimeError(f'SMS provider returned HTTP {response.status}.')
        else:
            raise RuntimeError('Unsupported notification channel.')
        delivery.status = 'sent'
        delivery.next_attempt_at = None
    except Exception as exc:
        delivery.status = 'pending_configuration' if 'not configured' in str(exc) else 'pending'
        delivery.error = str(exc)
        delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=min(60, 5 * (2 ** min(delivery.attempt_count - 1, 3))))
    delivery.attempted_at = datetime.now(timezone.utc)
    notification.delivery_status = delivery.status
    db.session.commit()
    return delivery


def retry_pending_deliveries(limit=25):
    now = datetime.now(timezone.utc)
    items = db.session.scalars(db.select(NotificationDelivery).where(NotificationDelivery.status.in_(['pending', 'pending_configuration']), or_(NotificationDelivery.next_attempt_at.is_(None), NotificationDelivery.next_attempt_at <= now)).order_by(NotificationDelivery.id).limit(limit)).all()
    return [deliver_notification(item.notification, item.channel, item.recipient, existing_delivery=item) for item in items]
