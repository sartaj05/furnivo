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
