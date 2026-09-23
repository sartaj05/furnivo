from backend.extensions import db
from backend.models import QuoteClientAccess, User


def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['ok'] is True


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
