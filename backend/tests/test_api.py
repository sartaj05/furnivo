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
