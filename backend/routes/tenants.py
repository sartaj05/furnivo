import re
from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models import Subscription, Tenant, TenantMembership
from ..services.audit import record_audit
from ..utils import current_user, roles_required

tenants_bp = Blueprint('tenants', __name__)


def _membership(tenant_id):
    return db.session.scalar(db.select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == current_user().id, TenantMembership.status == 'Active'))


@tenants_bp.get('')
@roles_required('admin', 'sales', 'designer', 'client')
def list_tenants():
    memberships = db.session.scalars(db.select(TenantMembership).where(TenantMembership.user_id == current_user().id, TenantMembership.status == 'Active').order_by(TenantMembership.id)).all()
    return jsonify({'memberships': [{'tenant': item.tenant.to_dict(), 'role': item.role, 'status': item.status, 'subscription': item.tenant.subscription.to_dict() if item.tenant and item.tenant.subscription else None} for item in memberships], 'active_tenant_id': current_user().active_tenant_id, 'mode': 'api'})


@tenants_bp.post('')
@roles_required('admin')
def create_tenant():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get('name', '')).strip()
    slug = re.sub(r'[^a-z0-9]+', '-', str(payload.get('slug') or name).lower()).strip('-')
    if not name or not slug:
        return jsonify({'message': 'Workspace name is required.'}), 400
    if db.session.scalar(db.select(Tenant).where(Tenant.slug == slug)):
        return jsonify({'message': 'Workspace slug already exists.'}), 409
    tenant = Tenant(name=name, slug=slug, plan='Starter', status='Trial', branding_json='{}')
    db.session.add(tenant); db.session.flush()
    db.session.add(TenantMembership(tenant_id=tenant.id, user_id=current_user().id, role='Owner', status='Active'))
    subscription = Subscription(tenant_id=tenant.id, provider='demo', plan='Starter', status='trialing', seats=5, monthly_amount=0)
    db.session.add(subscription); current_user().active_tenant_id = tenant.id
    record_audit(current_user().id, 'Tenant workspace created', 'tenant', tenant.id, tenant.slug)
    db.session.commit()
    return jsonify({'tenant': tenant.to_dict(), 'subscription': subscription.to_dict(), 'mode': 'api'}), 201


@tenants_bp.post('/<int:tenant_id>/switch')
@roles_required('admin', 'sales', 'designer', 'client')
def switch_tenant(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    if not _membership(tenant.id): return jsonify({'message': 'You do not have access to this workspace.'}), 403
    current_user().active_tenant_id = tenant.id
    record_audit(current_user().id, 'Tenant workspace switched', 'tenant', tenant.id, tenant.slug)
    db.session.commit()
    return jsonify({'tenant': tenant.to_dict(), 'active_tenant_id': tenant.id, 'mode': 'api'})


@tenants_bp.patch('/<int:tenant_id>/subscription')
@roles_required('admin')
def update_subscription(tenant_id):
    tenant = db.get_or_404(Tenant, tenant_id)
    if not _membership(tenant.id): return jsonify({'message': 'You do not have access to this workspace.'}), 403
    payload = request.get_json(silent=True) or {}; subscription = tenant.subscription
    if not subscription: subscription = Subscription(tenant_id=tenant.id); db.session.add(subscription)
    subscription.plan = str(payload.get('plan', subscription.plan or 'Starter')).strip()
    subscription.seats = max(int(payload.get('seats', subscription.seats or 5)), 1)
    subscription.status = str(payload.get('status', subscription.status or 'trialing')).strip()
    tenant.plan = subscription.plan; tenant.status = 'Active' if subscription.status == 'active' else 'Trial'
    record_audit(current_user().id, 'Tenant subscription updated', 'subscription', tenant.id, subscription.plan)
    db.session.commit()
    return jsonify({'tenant': tenant.to_dict(), 'subscription': subscription.to_dict(), 'mode': 'api'})
