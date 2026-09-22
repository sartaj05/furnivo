from ..extensions import db
from ..models import AuditLog


def record_audit(user_id, action, resource_type, resource_id='', detail=''):
    db.session.add(AuditLog(user_id=user_id, action=action, resource_type=resource_type, resource_id=str(resource_id or ''), detail=detail))
