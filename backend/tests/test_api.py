import hashlib
import hmac
import io
import json
import time

from backend.extensions import db
from backend.models import QuoteClientAccess, User
from backend.routes.auth import _failed_logins


def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['ok'] is True


def test_tenant_plans_branding_and_checkout(client, admin_headers):
    plans = client.get('/api/tenants/plans')
    assert plans.status_code == 200
    assert plans.json['plans']['Growth']['limits']['users'] == 15
    tenants = client.get('/api/tenants', headers=admin_headers)
    tenant_id = tenants.json['memberships'][0]['tenant']['id']
    branding = client.patch(f'/api/tenants/{tenant_id}/branding', headers=admin_headers, json={'primary_color': '#234b3c', 'support_email': 'support@furnivo.test'})
    assert branding.status_code == 200
    assert branding.json['tenant']['branding']['primary_color'] == '#234b3c'
    checkout = client.post(f'/api/tenants/{tenant_id}/subscription/checkout', headers=admin_headers, json={'plan': 'Growth'})
    assert checkout.status_code == 200
    assert checkout.json['plan'] == 'Growth'


def test_payment_provider_status_and_signed_webhook(monkeypatch, client, admin_headers):
    status = client.get('/api/payments/provider-status', headers=admin_headers)
    assert status.status_code == 200
    assert status.json['provider']['provider'] == 'demo'
    assert 'webhooks' in status.json['provider']['capabilities']

    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'razorpay-test-secret')
    payload = json.dumps({'external_id': 'missing-payment', 'status': 'paid'}).encode()
    signature = hmac.new(b'razorpay-test-secret', payload, hashlib.sha256).hexdigest()
    signed = client.post('/api/payments/webhook/razorpay', data=payload, content_type='application/json', headers={'X-Razorpay-Signature': signature})
    assert signed.status_code == 404

    stale_signature = hmac.new(b'razorpay-test-secret', payload, hashlib.sha256).hexdigest()
    invalid = client.post('/api/payments/webhook/stripe', data=payload, content_type='application/json', headers={'Stripe-Signature': f't={int(time.time()) - 600},v1={stale_signature}'})
    assert invalid.status_code == 401


def test_public_contact_inquiry_creates_new_lead(client):
    response = client.post('/api/leads/public', json={
        'name': 'Nisha Kapoor',
        'company': 'Kapoor Studio',
        'email': 'nisha@example.com',
        'phone': '+91 98765 43210',
        'interest': 'Design consultation',
        'message': 'We need help managing custom furniture quotations for our next project.',
    })
    assert response.status_code == 201
    assert response.json['item']['source'] == 'Website contact'
    assert response.json['item']['interest'] == 'Design consultation'
    assert response.json['item']['message'].startswith('We need help')


def test_login_and_protected_catalog(client, admin_headers):
    assert admin_headers['Authorization'].startswith('Bearer ')
    response = client.get('/api/products', headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json['items']) >= 3


def test_client_cannot_access_admin_quotes(client):
    login = client.post('/api/auth/login', json={'email': 'client@furnivo.demo', 'password': 'client123'})
    response = client.get('/api/quotes', headers={'Authorization': f"Bearer {login.json['token']}"})
    assert response.status_code == 403


def test_production_and_operations_endpoints(client, admin_headers):
    production = client.get('/api/production', headers=admin_headers)
    operations = client.get('/api/ops/health', headers=admin_headers)
    assert production.status_code == 200
    assert production.json['items']
    assert operations.status_code == 200
    assert operations.json['database'] == 'ok'


def test_deployment_readiness_endpoint(client, admin_headers):
    response = client.get('/api/ops/deployment-checks', headers=admin_headers)
    assert response.status_code == 200
    assert response.json['environment'] == 'test'
    assert response.json['mode'] == 'api'
    assert len(response.json['checks']) >= 4


def test_background_worker_status_and_retry(client, admin_headers):
    status = client.get('/api/data-admin/worker-status', headers=admin_headers)
    assert status.status_code == 200
    assert status.json['worker']['retryable'] is True
    created = client.post('/api/data-admin/jobs', headers=admin_headers, json={'job_type': 'catalog-reindex'})
    assert created.status_code == 202
    assert created.json['item']['status'] in {'Queued', 'Running', 'Complete'}


def test_security_policy_and_login_lockout(client, app):
    app.config['LOGIN_MAX_ATTEMPTS'] = 2
    app.config['LOGIN_LOCKOUT_MINUTES'] = 15
    for _ in range(2):
        failed = client.post('/api/auth/login', json={'email': 'admin@furnivo.demo', 'password': 'wrong-password'})
        assert failed.status_code == 401
    locked = client.post('/api/auth/login', json={'email': 'admin@furnivo.demo', 'password': 'wrong-password'})
    assert locked.status_code == 429
    login = client.post('/api/auth/login', json={'email': 'sales@furnivo.demo', 'password': 'sales123'})
    security = client.get('/api/auth/security', headers={'Authorization': f"Bearer {login.json['token']}"})
    assert security.status_code == 200
    assert security.json['policy']['max_login_attempts'] == 2
    _failed_logins.clear()


def test_backup_verification_is_admin_only(client, admin_headers):
    missing = client.get('/api/ops/backups/missing.db/verify', headers=admin_headers)
    assert missing.status_code == 404
    forbidden = client.get('/api/ops/backups/missing.db/verify')
    assert forbidden.status_code in {401, 404, 422}


def test_notification_provider_status_and_sms_configuration(client, admin_headers):
    status = client.get('/api/notifications/provider-status', headers=admin_headers)
    assert status.status_code == 200
    assert set(status.json['channels']) >= {'email', 'whatsapp', 'sms'}
    notifications = client.get('/api/notifications', headers=admin_headers)
    item_id = notifications.json['items'][0]['id']
    sms = client.post(f'/api/notifications/{item_id}/deliver', headers=admin_headers, json={'channel': 'sms', 'recipient': '+919999999999'})
    assert sms.status_code == 200
    assert sms.json['item']['status'] == 'pending_configuration'


def test_automation_rules_can_be_toggled(client, admin_headers):
    rules = client.get('/api/business/automation/rules', headers=admin_headers)
    assert rules.status_code == 200
    event = rules.json['rules'][0]['event']
    updated = client.patch(f'/api/business/automation/rules/{event}', headers=admin_headers, json={'enabled': False})
    assert updated.status_code == 200
    assert updated.json['rule']['enabled'] is False
    preview = client.post('/api/business/automation/preview', headers=admin_headers, json={'event': event})
    assert preview.status_code == 200
    assert preview.json['preview']['enabled'] is False
    updated = client.patch(f'/api/business/automation/rules/{event}', headers=admin_headers, json={'enabled': True})
    assert updated.status_code == 200


def test_supplier_portal_token_scopes_purchase_orders(client, admin_headers):
    suppliers = client.get('/api/procurement/suppliers', headers=admin_headers)
    supplier_id = suppliers.json['items'][0]['id']
    invite = client.post('/api/procurement/supplier-portal/invites', headers=admin_headers, json={'supplier_id': supplier_id})
    assert invite.status_code == 201
    token = invite.json['token']
    portal = client.get(f'/api/procurement/supplier-portal/{token}')
    assert portal.status_code == 200
    assert portal.json['supplier']['id'] == supplier_id


def test_profitability_breakdown_and_forecast_confidence(client, admin_headers):
    response = client.get('/api/analytics', headers=admin_headers)
    assert response.status_code == 200
    assert set(response.json['profitability']['cost_breakdown']) >= {'material', 'labor', 'wastage', 'shipping', 'discounts', 'taxes'}
    assert 0 <= response.json['forecast']['confidence_percent'] <= 95


def test_client_workspace_records_are_scoped(client):
    login = client.post('/api/auth/login', json={'email': 'client@furnivo.demo', 'password': 'client123'})
    headers = {'Authorization': f"Bearer {login.json['token']}"}
    warranties = client.get('/api/service/warranties', headers=headers)
    visits = client.get('/api/field', headers=headers)
    approvals = client.get('/api/access/approvals', headers=headers)
    assert warranties.status_code == 200
    assert all(item['order_number'] == 'ORD-1001' for item in warranties.json['items'])
    assert visits.status_code == 200
    assert all(item['order_number'] == 'ORD-1001' for item in visits.json['items'])
    assert approvals.status_code == 403


def test_notification_delivery_is_retryable(client, admin_headers):
    notifications = client.get('/api/notifications', headers=admin_headers)
    notification_id = notifications.json['items'][0]['id']
    delivery = client.post(f'/api/notifications/{notification_id}/deliver', headers=admin_headers, json={'channel': 'email', 'recipient': 'demo@example.com'})
    assert delivery.status_code == 200
    assert delivery.json['item']['attempt_count'] == 1
    retry = client.post(f"/api/notifications/deliveries/{delivery.json['item']['id']}/retry", headers=admin_headers)
    assert retry.status_code == 200
    assert retry.json['item']['attempt_count'] == 2


def test_furniture_visual_configuration_can_be_saved_and_quoted(client, admin_headers):
    options = client.get('/api/quote-config/options', headers=admin_headers)
    assert options.status_code == 200
    assert options.json['options']['dimension_surcharge_percent'] == 8

    customers = client.get('/api/customers', headers=admin_headers)
    customer_id = customers.json['items'][0]['id']
    saved = client.post('/api/quote-config/configurations', headers=admin_headers, json={
        'name': 'Visual living room set',
        'room': 'Living room',
        'customer_id': customer_id,
        'items': [{
            'product_id': 1,
            'variant_id': 1,
            'quantity': 2,
            'options': {'material': 'Walnut', 'fabric': 'Velvet', 'color': 'Sage', 'finish': 'Natural oil'},
            'dimensions': {'width': 2800, 'height': 800, 'depth': 980},
        }],
    })
    assert saved.status_code == 201
    configuration = saved.json['item']
    assert configuration['configuration_number'].startswith('CFG-')
    assert configuration['items'][0]['options']['material'] == 'Walnut'
    assert configuration['items'][0]['unit_price'] > 78500

    quote = client.post('/api/quotes', headers=admin_headers, json={
        'configuration_id': configuration['id'],
        'customer_id': customer_id,
        'discount_percent': 0,
        'tax_percent': 18,
    })
    assert quote.status_code == 201
    assert quote.json['item']['items'][0]['description'].startswith('Aster Modular Sofa')
    configurations = client.get('/api/quote-config/configurations', headers=admin_headers)
    linked = next(item for item in configurations.json['items'] if item['id'] == configuration['id'])
    assert linked['status'] == 'Quoted'
    assert linked['quote_id'] == quote.json['item']['id']


def test_execution_procurement_and_delivery_workflows(client, admin_headers):
    visits = client.get('/api/field', headers=admin_headers)
    visit_id = visits.json['items'][0]['id']
    checked_in = client.post(f'/api/field/{visit_id}/check-in', headers=admin_headers, json={'gps_lat': 28.61, 'gps_lng': 77.21})
    assert checked_in.status_code == 200
    material = client.post(f'/api/field/{visit_id}/materials', headers=admin_headers, json={'name': 'Installation anchors', 'quantity': 4, 'movement': 'issue'})
    assert material.status_code == 200
    assert material.json['item']['materials'][0]['movement'] == 'issue'
    checked_out = client.post(f'/api/field/{visit_id}/check-out', headers=admin_headers)
    assert checked_out.status_code == 200
    assert checked_out.json['item']['status'] == 'Completed'

    performance = client.get('/api/procurement/supplier-performance', headers=admin_headers)
    assert performance.status_code == 200
    schedules = client.get('/api/schedules', headers=admin_headers)
    schedule_id = schedules.json['items'][0]['id']
    confirmed = client.post(f'/api/schedules/{schedule_id}/confirm', headers=admin_headers)
    assert confirmed.status_code == 200
    proof = client.post(f'/api/schedules/{schedule_id}/proof', headers=admin_headers, json={'proof_url': 'https://demo.invalid/proof.jpg'})
    assert proof.status_code == 200
    assert proof.json['item']['status'] == 'Completed'
    signoff = client.post(f'/api/schedules/{schedule_id}/signoff', headers=admin_headers, json={'signature': 'Aarav Customer', 'accepted': True})
    assert signoff.status_code == 200
    assert signoff.json['signoff']['accepted'] is True


def test_accounting_security_notifications_routes_and_service_feedback(client, admin_headers):
    summary = client.get('/api/payment-reconciliation/summary', headers=admin_headers)
    assert summary.status_code == 200
    assert summary.json['summary']['invoice_count'] >= 1
    reminders = client.post('/api/payment-reconciliation/reminders', headers=admin_headers)
    assert reminders.status_code == 200

    branch = client.post('/api/branches', headers=admin_headers, json={'name': 'Mumbai Studio', 'code': 'MUM', 'address': 'Mumbai', 'manager': 'Demo Manager'})
    assert branch.status_code == 201
    users = client.get('/api/access/users', headers=admin_headers)
    assigned = client.post(f"/api/branches/{branch.json['item']['id']}/users", headers=admin_headers, json={'user_id': users.json['items'][0]['user']['id'], 'is_primary': True})
    assert assigned.status_code == 201

    broadcast = client.post('/api/notifications/broadcast', headers=admin_headers, json={'title': 'Production update', 'body': 'Workshop schedule refreshed.', 'channel': 'in_app', 'roles': ['admin']})
    assert broadcast.status_code == 200
    delivery_summary = client.get('/api/notifications/delivery-summary', headers=admin_headers)
    assert delivery_summary.status_code == 200

    route = client.get('/api/schedules/route-plan', headers=admin_headers)
    assert route.status_code == 200
    optimized = client.post('/api/schedules/route-plan/optimize', headers=admin_headers)
    assert optimized.status_code == 200

    tickets = client.get('/api/service/tickets', headers=admin_headers)
    ticket_id = tickets.json['items'][0]['id']
    feedback = client.post(f'/api/service/tickets/{ticket_id}/feedback', headers=admin_headers, json={'rating': 5, 'feedback': 'Fast resolution.'})
    assert feedback.status_code == 200
    assert feedback.json['item']['customer_rating'] == 5


def test_accounting_status_exports_and_entity_validation(client, admin_headers):
    integrations = client.get('/api/integrations', headers=admin_headers)
    assert integrations.status_code == 200
    assert integrations.json['status']['providers']
    connection_id = integrations.json['connections'][0]['id']

    status = client.get('/api/integrations/accounting-status', headers=admin_headers)
    assert status.status_code == 200
    assert status.json['status']['connections'][0]['credentials_configured'] is True

    export = client.post(f'/api/integrations/{connection_id}/export', headers=admin_headers, json={'entity': 'invoices'})
    assert export.status_code == 200
    assert export.json['export']['record_count'] >= 1
    assert export.json['export']['delivery'] == 'adapter-ready'

    sync = client.post(f'/api/integrations/{connection_id}/sync', headers=admin_headers, json={'entity': 'payments'})
    assert sync.status_code == 200
    assert sync.json['item']['records_synced'] >= 0

    invalid = client.post(f'/api/integrations/{connection_id}/export', headers=admin_headers, json={'entity': 'customers'})
    assert invalid.status_code == 400


def test_scheduling_portal_recommendations_forecast_and_quality(client, admin_headers):
    jobs = client.get('/api/production', headers=admin_headers)
    job_id = jobs.json['items'][0]['id']
    task = client.post('/api/production/schedule', headers=admin_headers, json={'production_job_id': job_id, 'name': 'Cutting plan', 'stage': 'Cutting', 'assigned_worker': 'Workshop A', 'machine': 'Panel saw'})
    assert task.status_code == 201
    capacity = client.get('/api/production/capacity', headers=admin_headers)
    assert capacity.status_code == 200
    inspection = client.post(f'/api/production/{job_id}/inspections', headers=admin_headers, json={'status': 'Passed', 'checklist': [{'item': 'Finish', 'passed': True}]})
    assert inspection.status_code == 201
    assert inspection.json['job']['status'] == 'Ready'

    forecast = client.get('/api/inventory/forecast', headers=admin_headers)
    assert forecast.status_code == 200
    recommendations = client.post('/api/recommendations', headers=admin_headers, json={'room': 'Living room', 'budget': 200000})
    assert recommendations.status_code == 200
    assert recommendations.json['items']

    login = client.post('/api/auth/login', json={'email': 'client@furnivo.demo', 'password': 'client123'})
    client_headers = {'Authorization': f"Bearer {login.json['token']}"}
    mobile = client.get('/api/portal/mobile-summary', headers=client_headers)
    assert mobile.status_code == 200
    assert 'next_schedules' in mobile.json


def test_production_planner_dependency_and_resource_conflicts(client, admin_headers):
    jobs = client.get('/api/production', headers=admin_headers).json['items']
    first = client.post('/api/production/schedule', headers=admin_headers, json={'production_job_id': jobs[0]['id'], 'name': 'Planner cut', 'stage': 'Cutting', 'assigned_worker': 'Planner Worker', 'machine': 'Planner Saw', 'planned_start': '2026-09-24T09:00:00+00:00', 'planned_end': '2026-09-24T11:00:00+00:00'})
    second = client.post('/api/production/schedule', headers=admin_headers, json={'production_job_id': jobs[0]['id'], 'name': 'Planner assembly', 'stage': 'Assembly', 'assigned_worker': 'Planner Worker', 'machine': 'Planner Saw', 'planned_start': '2026-09-24T10:00:00+00:00', 'planned_end': '2026-09-24T12:00:00+00:00'})
    assert first.status_code == 201 and second.status_code == 201
    schedule = client.get('/api/production/schedule', headers=admin_headers)
    assert schedule.status_code == 200
    assert any(item['task_id'] == second.json['item']['id'] for item in schedule.json['conflicts'])
    moved = client.patch(f"/api/production/schedule/{second.json['item']['id']}", headers=admin_headers, json={'dependency_id': first.json['item']['id']})
    assert moved.status_code == 200
    assert moved.json['conflicts']
    invalid = client.patch(f"/api/production/schedule/{second.json['item']['id']}", headers=admin_headers, json={'planned_start': '2026-09-24T12:00:00+00:00', 'planned_end': '2026-09-24T11:00:00+00:00'})
    assert invalid.status_code == 400


def test_inventory_forecast_controls_and_stockout_metrics(client, admin_headers):
    forecast = client.get('/api/inventory/forecast?days=90&seasonal_factor=1.25&lead_time_days=21', headers=admin_headers)
    assert forecast.status_code == 200
    assert forecast.json['horizon_days'] == 90
    assert forecast.json['seasonal_factor'] == 1.25
    assert forecast.json['lead_time_days'] == 21
    assert forecast.json['items']
    assert 'safety_stock' in forecast.json['items'][0]
    invalid = client.get('/api/inventory/forecast?days=bad', headers=admin_headers)
    assert invalid.status_code == 400


def test_mobile_workshop_task_execution_and_material_issue(client, admin_headers):
    jobs = client.get('/api/production', headers=admin_headers).json['items']
    created = client.post('/api/production/schedule', headers=admin_headers, json={'production_job_id': jobs[0]['id'], 'name': 'Mobile execution task', 'stage': 'Assembly', 'assigned_worker': 'Mobile Worker'})
    assert created.status_code == 201
    task_id = created.json['item']['id']
    mobile = client.get('/api/production/mobile/tasks', headers=admin_headers, query_string={'code': str(task_id)})
    assert mobile.status_code == 200
    assert len(mobile.json['items']) == 1
    updated = client.patch(f'/api/production/mobile/tasks/{task_id}', headers=admin_headers, json={'status': 'In progress', 'actual_minutes': 35})
    assert updated.status_code == 200
    assert updated.json['item']['actual_minutes'] == 35
    inventory = client.get('/api/inventory', headers=admin_headers).json['items'][0]
    movement = client.post(f'/api/production/mobile/tasks/{task_id}/materials', headers=admin_headers, json={'inventory_id': inventory['id'], 'quantity': 0.1, 'movement': 'issue'})
    assert movement.status_code == 200
    assert movement.json['movement']['movement_type'] == 'Workshop issue'

def test_planning_profitability_timeline_and_automation(client, admin_headers):
    planning = client.get('/api/business/planning', headers=admin_headers)
    assert planning.status_code == 200
    assert planning.json['planning']['summary']['jobs'] >= 1
    assert planning.json['planning']['summary']['estimated_cost'] > 0

    reserved = client.post('/api/business/planning/reserve', headers=admin_headers)
    assert reserved.status_code == 200
    analytics = client.get('/api/analytics', headers=admin_headers)
    assert analytics.status_code == 200
    assert analytics.json['profitability']['gross_profit'] >= 0

    templates = client.get('/api/business/automation', headers=admin_headers)
    assert templates.status_code == 200
    preview = client.post('/api/business/automation/preview', headers=admin_headers, json={'event': 'production_update', 'variables': {'order_number': 'ORD-1001', 'status': 'Ready'}})
    assert preview.status_code == 200
    assert 'ORD-1001' in preview.json['preview']['body']

    portal_login = client.post('/api/auth/login', json={'email': 'client@furnivo.demo', 'password': 'client123'})
    portal_headers = {'Authorization': f"Bearer {portal_login.json['token']}"}
    portal = client.get('/api/portal', headers=portal_headers)
    assert portal.status_code == 200
    assert portal.json['projects'][0]['timeline']


def test_quote_to_payment_automation(client, app):
    sales_login = client.post('/api/auth/login', json={'email': 'sales@furnivo.demo', 'password': 'sales123'})
    sales_headers = {'Authorization': f"Bearer {sales_login.json['token']}"}
    quote_response = client.post('/api/quotes', headers=sales_headers, json={
        'customer': 'Automation Studio',
        'items': [{'product_id': 1, 'quantity': 1}],
        'tax_percent': 18,
    })
    assert quote_response.status_code == 201
    quote_id = quote_response.json['item']['database_id']

    with app.app_context():
        client_user = db.session.scalar(db.select(User).where(User.email == 'client@furnivo.demo'))
        db.session.add(QuoteClientAccess(quote_id=quote_id, user_id=client_user.id))
        db.session.commit()

    client_login = client.post('/api/auth/login', json={'email': 'client@furnivo.demo', 'password': 'client123'})
    client_headers = {'Authorization': f"Bearer {client_login.json['token']}"}
    approved = client.post(f'/api/quotes/{quote_id}/client-response', headers=client_headers, json={'action': 'Approved'})
    assert approved.status_code == 200
    assert approved.json['automation']['contract_created'] is True
    contract_id = approved.json['automation']['contract']['id']

    signed = client.post(f'/api/contracts/{contract_id}/sign', headers=client_headers, json={'signature_text': 'Riya Client'})
    assert signed.status_code == 200
    assert signed.json['automation']['created'] is True
    invoice = signed.json['automation']['invoice']
    assert invoice['invoice_type'] == 'Deposit'
    assert invoice['deposit_percent'] == 30
    assert invoice['status'] == 'Sent'

    checkout_headers = {**client_headers, 'Idempotency-Key': 'automation-checkout-1'}
    checkout = client.post(f"/api/payments/invoices/{invoice['id']}/checkout", headers=checkout_headers)
    assert checkout.status_code == 200
    external_id = checkout.json['item']['external_id']
    webhook = client.post('/api/payments/webhook/demo', json={'external_id': external_id, 'status': 'paid'})
    assert webhook.status_code == 200

    orders = client.get('/api/orders', headers=client_headers)
    matching_order = next(item for item in orders.json['items'] if item['quote_id'] == quote_id)
    assert matching_order['status'] == 'Confirmed'
    invoices = client.get('/api/invoices', headers=client_headers)
    matching_invoice = next(item for item in invoices.json['items'] if item['id'] == invoice['id'])
    assert matching_invoice['status'] == 'Paid'


def test_ai_collaboration_predictive_and_tenant_features(client, admin_headers):
    design = client.post('/api/design-assistant', headers=admin_headers, json={'room': 'Bedroom', 'style': 'Japandi', 'color': 'Ivory', 'budget': 120000})
    assert design.status_code == 200
    assert design.json['brief']['layout']
    assert design.json['brief']['provider'] == 'demo-fallback'

    live = client.get('/api/live/updates', headers=admin_headers)
    assert live.status_code == 200
    assert 'items' in live.json

    predictive = client.get('/api/analytics/predictive', headers=admin_headers)
    assert predictive.status_code == 200
    assert 'purchase_recommendations' in predictive.json
    assert 'quality' in predictive.json

    tenant = client.post('/api/tenants', headers=admin_headers, json={'name': 'Jaipur Studio'})
    assert tenant.status_code == 201
    tenant_id = tenant.json['tenant']['id']
    listed = client.get('/api/tenants', headers=admin_headers)
    assert any(item['tenant']['id'] == tenant_id for item in listed.json['memberships'])
    switched = client.post(f'/api/tenants/{tenant_id}/switch', headers=admin_headers)
    assert switched.status_code == 200
    assert switched.json['active_tenant_id'] == tenant_id


def test_ai_design_room_upload_and_enriched_brief(client, admin_headers):
    upload = client.post('/api/uploads/design-room', headers=admin_headers, data={'file': (io.BytesIO(b'fake-image'), 'room.jpg')}, content_type='multipart/form-data')
    assert upload.status_code == 201
    assert upload.json['item']['entity_type'] == 'design_room'
    design = client.post('/api/design-assistant', headers=admin_headers, json={'room': 'Bedroom', 'style': 'Japandi', 'material': 'Oak', 'color': 'Ivory', 'budget': 120000, 'image_url': upload.json['item']['url']})
    assert design.status_code == 200
    assert design.json['brief']['design_inputs']['image_url'] == upload.json['item']['url']
    assert design.json['brief']['next_steps']


def test_api_preserves_expected_http_errors_and_demo_ai_budget_order(client, admin_headers):
    missing = client.post('/api/tenants/999999/switch', headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json['message']
    wrong_method = client.post('/api/products/1', headers=admin_headers, json={})
    assert wrong_method.status_code == 405

    design = client.post('/api/design-assistant', headers=admin_headers, json={'room': 'Living room', 'budget': 13000})
    assert design.status_code == 200
    prices = [item['product']['price'] for item in design.json['brief']['recommendations']]
    assert prices and prices[0] <= 13000


def test_forgot_and_reset_password_flow(client):
    requested = client.post('/api/auth/forgot-password', json={'email': 'admin@furnivo.demo'})
    assert requested.status_code == 200
    token = requested.json['reset_token']
    assert token

    reset = client.post('/api/auth/reset-password', json={'token': token, 'password': 'NewAdmin12345'})
    assert reset.status_code == 200
    login = client.post('/api/auth/login', json={'email': 'admin@furnivo.demo', 'password': 'NewAdmin12345'})
    assert login.status_code == 200

    reused = client.post('/api/auth/reset-password', json={'token': token, 'password': 'AnotherAdmin12345'})
    assert reused.status_code == 400
    unknown = client.post('/api/auth/forgot-password', json={'email': 'unknown@example.com'})
    assert unknown.status_code == 200
    assert unknown.json.get('reset_token') is None
