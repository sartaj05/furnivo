from werkzeug.security import generate_password_hash
from .extensions import db
from .models import AccessPermission, ApprovalRequest, AuditLog, BomItem, Contract, CreditNote, Customer, CustomerPricing, Department, DeliverySchedule, EInvoice, FieldVisit, IntegrationConnection, InventoryItem, Invoice, Lead, LeadNote, LeadTask, Notification, Order, PaymentReconciliation, Product, ProductVariant, ProductionJob, ProjectOwnership, PurchaseOrder, PurchaseOrderItem, Quote, QuoteClientAccess, QuoteItem, QuotePreset, ProjectUpdate, ReturnRequest, ServiceTicket, StockMovement, Subscription, Supplier, SyncRun, Tenant, TenantMembership, User, UserDepartment, Warehouse, WarehouseStock, Warranty


DEMO_PRODUCTS = [
    {"sku": "FUR-SOF-101", "name": "Aster Modular Sofa", "category": "Furniture", "price": 78500, "cost_price": 42000, "unit": "set", "material": "Oak frame, performance fabric", "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=80"},
    {"sku": "INT-LGT-204", "name": "Halo Pendant Light", "category": "Interiors", "price": 12400, "cost_price": 6200, "unit": "piece", "material": "Powder-coated metal, frosted glass", "image": "https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=900&q=80"},
    {"sku": "BLD-PNL-310", "name": "Terra Fluted Wall Panel", "category": "Building Material", "price": 920, "cost_price": 430, "unit": "sq.ft", "material": "WPC acoustic panel", "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80"},
]

DEMO_USERS = [
    ('Aarav Admin', 'admin@furnivo.demo', 'admin123', 'admin'),
    ('Meera Sales', 'sales@furnivo.demo', 'sales123', 'sales'),
    ('Kabir Designer', 'designer@furnivo.demo', 'design123', 'designer'),
    ('Riya Client', 'client@furnivo.demo', 'client123', 'client'),
    ('Neel Workshop', 'workshop@furnivo.demo', 'workshop123', 'workshop_operator'),
    ('Arjun Installer', 'installer@furnivo.demo', 'install123', 'installer'),
    ('Diya Accountant', 'accountant@furnivo.demo', 'account123', 'accountant'),
]


def seed_database():
    db.create_all()
    for name, email, password, role in DEMO_USERS:
        existing = db.session.scalar(db.select(User).where(User.email == email))
        if existing:
            continue
        db.session.add(
            User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
        )
    db.session.commit()
    seed_tenants()

    for data in DEMO_PRODUCTS:
        if db.session.scalar(db.select(Product).where(Product.sku == data["sku"])):
            continue
        db.session.add(Product(**data))
    db.session.commit()

    sofa = db.session.scalar(db.select(Product).where(Product.sku == "FUR-SOF-101"))
    if sofa and not sofa.variants:
        sofa.variants.extend([
            ProductVariant(sku="FUR-SOF-101-SAND", finish="Sand Boucle", width_mm=2600, height_mm=780, depth_mm=980, price_delta=0),
            ProductVariant(sku="FUR-SOF-101-OLIVE", finish="Olive Performance", width_mm=2600, height_mm=780, depth_mm=980, price_delta=4500),
        ])
        db.session.commit()

    seed_customers()
    seed_quotes()
    seed_client_quote_access()
    seed_orders()
    seed_inventory()
    seed_notifications()
    seed_invoices()
    seed_procurement()
    seed_audit_logs()
    seed_schedules()
    seed_warehouses()
    seed_returns()
    seed_configurator()
    seed_production()
    seed_reconciliation()
    seed_contracts()
    seed_gst()
    seed_leads()
    seed_access_controls()
    seed_service_management()
    seed_integrations()
    seed_field_operations()


def seed_tenants():
    tenant = db.session.scalar(db.select(Tenant).where(Tenant.slug == 'furnivo-demo'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if not tenant:
        tenant = Tenant(name='Furnivo Demo Workspace', slug='furnivo-demo', plan='Starter', status='Trial', branding_json='{}')
        db.session.add(tenant); db.session.flush()
    if not db.session.scalar(db.select(Subscription).where(Subscription.tenant_id == tenant.id)):
        db.session.add(Subscription(tenant_id=tenant.id, provider='demo', plan='Starter', status='trialing', seats=5, monthly_amount=0))
    for user in db.session.scalars(db.select(User)).all():
        if not db.session.scalar(db.select(TenantMembership).where(TenantMembership.tenant_id == tenant.id, TenantMembership.user_id == user.id)):
            db.session.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role='Owner' if user.id == admin.id else 'Member', status='Active'))
        if user.active_tenant_id is None: user.active_tenant_id = tenant.id
    db.session.commit()


def seed_access_controls():
    department_data = [('Sales', 'Quotations, customer relationships, and approvals.'), ('Design', 'Design delivery and project specifications.'), ('Operations', 'Production, delivery, and service execution.'), ('Finance', 'Invoices, payments, GST, and accounting exports.')]
    departments = {}
    for name, description in department_data:
        department = db.session.scalar(db.select(Department).where(Department.name == name))
        if not department:
            department = Department(name=name, description=description); db.session.add(department); db.session.flush()
        departments[name] = department
    db.session.commit()

    permission_map = {
        'admin': [('*', 'global')],
        'sales': [('quotes.create', 'team'), ('quotes.discount', 'approval'), ('customers.view', 'team'), ('orders.manage', 'team'), ('payments.manage', 'team'), ('reports.view', 'team')],
        'designer': [('catalog.configure', 'own'), ('production.manage', 'assigned'), ('inventory.view', 'assigned'), ('orders.view', 'assigned')],
        'client': [('portal.view', 'own'), ('quotes.respond', 'own'), ('payments.view', 'own'), ('service.create', 'own')],
        'workshop_operator': [('production.execute', 'assigned'), ('inventory.issue', 'assigned'), ('quality.handoff', 'assigned')],
        'installer': [('delivery.execute', 'assigned'), ('installation.proof', 'assigned'), ('customer.signoff', 'assigned')],
        'accountant': [('invoices.view', 'global'), ('payments.manage', 'global'), ('gst.manage', 'global'), ('accounting.export', 'global')],
    }
    for role, permissions in permission_map.items():
        for user in db.session.scalars(db.select(User).where(User.role == role)).all():
            if role == 'admin' and not user.approval_limit:
                user.approval_limit = 10000000
            elif role == 'sales' and not user.approval_limit:
                user.approval_limit = 150000
            for permission, scope in permissions:
                if not db.session.scalar(db.select(AccessPermission).where(AccessPermission.user_id == user.id, AccessPermission.permission == permission, AccessPermission.scope == scope)):
                    db.session.add(AccessPermission(user_id=user.id, permission=permission, scope=scope))
            department_name = {'admin': 'Operations', 'sales': 'Sales', 'designer': 'Design', 'workshop_operator': 'Operations', 'installer': 'Operations', 'accountant': 'Finance'}.get(role)
            if department_name and not db.session.scalar(db.select(UserDepartment).where(UserDepartment.user_id == user.id, UserDepartment.department_id == departments[department_name].id)):
                db.session.add(UserDepartment(user_id=user.id, department_id=departments[department_name].id, role_title='Administrator' if role == 'admin' else role.title()))
    db.session.commit()

    quote = db.session.scalar(db.select(Quote).where(Quote.quote_number == 'Q-1042'))
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    sales = db.session.scalar(db.select(User).where(User.role == 'sales'))
    designer = db.session.scalar(db.select(User).where(User.role == 'designer'))
    workshop = db.session.scalar(db.select(User).where(User.role == 'workshop_operator'))
    installer = db.session.scalar(db.select(User).where(User.role == 'installer'))
    admin = db.session.scalar(db.select(User).where(User.role == 'admin'))
    if order:
        for owner in (sales, designer, workshop, installer):
            if owner and not db.session.scalar(db.select(ProjectOwnership).where(ProjectOwnership.order_id == order.id, ProjectOwnership.user_id == owner.id)):
                db.session.add(ProjectOwnership(order_id=order.id, user_id=owner.id, assigned_by_id=admin.id if admin else owner.id))
        db.session.commit()
    if quote and sales and not db.session.scalar(db.select(ApprovalRequest).where(ApprovalRequest.resource_id == quote.quote_number)):
        db.session.add(ApprovalRequest(request_type='Discount', resource_type='quote', resource_id=quote.quote_number, amount=186400, detail='Approval required for a customer discount above the sales threshold.', requested_by_id=sales.id))
        db.session.commit()


def seed_service_management():
    if db.session.scalar(db.select(Warranty).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    customer = db.session.scalar(db.select(Customer).where(Customer.company == 'Northline Studio'))
    product = db.session.scalar(db.select(Product).where(Product.sku == 'FUR-SOF-101'))
    admin = db.session.scalar(db.select(User).where(User.role == 'admin'))
    sales = db.session.scalar(db.select(User).where(User.role == 'sales'))
    if not order or not admin:
        return
    warranty = Warranty(warranty_number='WAR-7001', order_id=order.id, product_id=product.id if product else None, customer_id=customer.id if customer else None, start_date=__import__('datetime').date(2026, 10, 20), end_date=__import__('datetime').date(2028, 10, 19), serial_number='AST-1001', coverage='Manufacturing defects, hardware, and installation issues')
    db.session.add(warranty); db.session.flush()
    db.session.add(ServiceTicket(ticket_number='SVC-8001', warranty_id=warranty.id, order_id=order.id, customer_id=customer.id if customer else None, subject='Post-installation alignment check', description='Customer requested a technician visit to verify the sofa modules after installation.', priority='High', status='Assigned', assigned_to_id=sales.id if sales else admin.id, sla_due=__import__('datetime').date(2026, 10, 24)))
    db.session.commit()


def seed_integrations():
    if db.session.scalar(db.select(IntegrationConnection).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.role == 'admin'))
    if admin:
        db.session.add(IntegrationConnection(name='Demo accounting workspace', provider='Zoho Books', external_account='Furnivo Demo Books', credentials_ref='env:ZOHO_BOOKS_TOKEN', status='Connected'))
        db.session.commit()


def seed_field_operations():
    if db.session.scalar(db.select(FieldVisit).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    schedule = db.session.scalar(db.select(DeliverySchedule).where(DeliverySchedule.order_id == order.id)) if order else None
    admin = db.session.scalar(db.select(User).where(User.role == 'admin'))
    sales = db.session.scalar(db.select(User).where(User.role == 'sales'))
    if order and admin:
        db.session.add(FieldVisit(order_id=order.id, schedule_id=schedule.id if schedule else None, visit_type='Installation', status='Scheduled', assigned_to_id=sales.id if sales else admin.id, scheduled_date=__import__('datetime').date(2026, 10, 20), qr_token='FURNIVO-DEMO1001', notes='Scan the project QR at arrival.', created_by_id=admin.id))
        db.session.commit()


def seed_quotes():
    if db.session.scalar(db.select(Quote).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.role == "admin"))
    sofa = db.session.scalar(db.select(Product).where(Product.sku == "FUR-SOF-101"))
    light = db.session.scalar(db.select(Product).where(Product.sku == "INT-LGT-204"))
    if not admin or not sofa:
        return
    customer = db.session.scalar(db.select(Customer).where(Customer.company == "Northline Studio"))
    quote = Quote(quote_number="Q-1042", customer_name="Northline Studio", customer_id=customer.id if customer else None, status="Sent", quote_date=__import__('datetime').date(2026, 9, 18), created_by_id=admin.id)
    quote.items = [QuoteItem(product_id=sofa.id, description=sofa.name, sku=sofa.sku, quantity=2, unit=sofa.unit, unit_price=sofa.price)]
    if light:
        quote.items.append(QuoteItem(product_id=light.id, description=light.name, sku=light.sku, quantity=2, unit=light.unit, unit_price=light.price))
    db.session.add(quote)
    db.session.commit()


def seed_customers():
    demo = [
        {"company": "Northline Studio", "contact_name": "Ishita Arora", "email": "projects@northline.demo", "phone": "+91 98100 21001", "project_address": "Defence Colony, New Delhi", "gstin": "07DEMO1234A1Z5"},
        {"company": "The Green House", "contact_name": "Rohan Sen", "email": "hello@greenhouse.demo", "phone": "+91 98100 21002", "project_address": "Gurugram, Haryana"},
        {"company": "Avenue Architects", "contact_name": "Neha Jain", "email": "studio@avenue.demo", "phone": "+91 98100 21003", "project_address": "Noida, Uttar Pradesh"},
    ]
    for data in demo:
        if not db.session.scalar(db.select(Customer).where(Customer.company == data["company"])):
            db.session.add(Customer(**data))
    db.session.commit()


def seed_leads():
    if db.session.scalar(db.select(Lead).limit(1)):
        return
    sales = db.session.scalar(db.select(User).where(User.role == "sales"))
    admin = db.session.scalar(db.select(User).where(User.role == "admin"))
    demo = [
        ("Sana Kapoor", "SK Atelier", "+91 98111 22334", "Website", "New", 240000, sales),
        ("Arjun Mehta", "Mehta Homes", "+91 98770 11228", "Referral", "Qualified", 510000, sales),
        ("Devika Rao", "Form & Field", "+91 98990 33001", "Instagram", "Proposal", 175000, admin),
        ("Neil Thomas", "NTH Build", "+91 97110 81020", "Exhibition", "Won", 690000, sales),
    ]
    for name, company, phone, source, stage, value, owner in demo:
        lead = Lead(name=name, company=company, phone=phone, source=source, stage=stage, value=value, owner_id=owner.id if owner else None)
        db.session.add(lead)
        db.session.flush()
        if stage != "Won":
            db.session.add(LeadTask(lead_id=lead.id, title="Follow up on material selection", due_date=__import__('datetime').date(2026, 9, 25), assigned_to_id=owner.id if owner else None))
        db.session.add(LeadNote(lead_id=lead.id, author_id=(owner or admin).id, body="Initial enquiry captured and qualification started."))
    db.session.commit()


def seed_client_quote_access():
    client = db.session.scalar(db.select(User).where(User.email == 'client@furnivo.demo'))
    quote = db.session.scalar(db.select(Quote).where(Quote.quote_number == 'Q-1042'))
    if not client or not quote:
        return
    existing = db.session.scalar(db.select(QuoteClientAccess).where(
        QuoteClientAccess.user_id == client.id,
        QuoteClientAccess.quote_id == quote.id,
    ))
    if not existing:
        db.session.add(QuoteClientAccess(user_id=client.id, quote_id=quote.id))
        db.session.commit()


def seed_orders():
    if db.session.scalar(db.select(Order).limit(1)):
        return
    quote = db.session.scalar(db.select(Quote).where(Quote.quote_number == 'Q-1042'))
    admin = db.session.scalar(db.select(User).where(User.role == 'admin'))
    if not quote or not admin:
        return
    order = Order(order_number='ORD-1001', quote_id=quote.id, customer_id=quote.customer_id, customer_name=quote.customer_name, production_status='In production', installation_status='Scheduled', created_by_id=admin.id, notes='Demo project order')
    db.session.add(order)
    db.session.flush()
    db.session.add(ProjectUpdate(order_id=order.id, body='Materials confirmed and production slot reserved.', author_id=admin.id))
    db.session.commit()


def seed_inventory():
    if db.session.scalar(db.select(InventoryItem).limit(1)):
        return
    products = db.session.scalars(db.select(Product).order_by(Product.id)).all()
    demo_stock = [(12, 2, 4, 'Oak & Co. Furnishings', 'Delhi warehouse'), (24, 5, 8, 'Halo Lighting Works', 'Delhi warehouse'), (1200, 300, 400, 'Terra Surfaces', 'Gurugram warehouse')]
    for product, values in zip(products, demo_stock):
        quantity, reserved, reorder, supplier, location = values
        db.session.add(InventoryItem(product_id=product.id, quantity=quantity, reserved_quantity=reserved, reorder_level=reorder, supplier=supplier, location=location))
    db.session.commit()


def seed_notifications():
    if db.session.scalar(db.select(Notification).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    client = db.session.scalar(db.select(User).where(User.email == 'client@furnivo.demo'))
    if admin:
        db.session.add(Notification(user_id=admin.id, type='task', title='Follow-up workspace ready', body='Review the active lead pipeline and open tasks.', related_type='lead', related_id=''))
    if client:
        db.session.add(Notification(user_id=client.id, type='quote', title='Quotation ready for review', body='Q-1042 is ready in your client portal.', related_type='quote', related_id='1'))
    db.session.commit()


def seed_invoices():
    if db.session.scalar(db.select(Invoice).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if not order or not admin:
        return
    db.session.add(Invoice(invoice_number='INV-2001', order_id=order.id, customer_id=order.customer_id, customer_name=order.customer_name, issue_date=__import__('datetime').date(2026, 9, 18), due_date=__import__('datetime').date(2026, 10, 3), status='Partially Paid', subtotal=order.quote.subtotal, tax_amount=order.quote.tax_amount, total=order.quote.total, amount_paid=50000, payment_link='/pay/INV-2001', created_by_id=admin.id))
    db.session.commit()


def seed_procurement():
    if db.session.scalar(db.select(Supplier).limit(1)):
        return
    supplier = Supplier(name='Oak & Co. Furnishings', email='orders@oakco.demo', phone='+91 98000 10001', notes='Primary timber and furniture supplier')
    db.session.add(supplier); db.session.flush()
    product = db.session.scalar(db.select(Product).where(Product.sku == 'FUR-SOF-101'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if product and admin:
        po = PurchaseOrder(po_number='PO-3001', supplier_id=supplier.id, status='Confirmed', order_date=__import__('datetime').date(2026, 9, 19), expected_date=__import__('datetime').date(2026, 10, 5), created_by_id=admin.id)
        po.items.append(PurchaseOrderItem(product_id=product.id, description=product.name, quantity=4, unit_cost=65000))
        db.session.add(po)
    db.session.commit()


def seed_audit_logs():
    if db.session.scalar(db.select(AuditLog).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if admin:
        db.session.add(AuditLog(user_id=admin.id, action='Seeded demo workspace', resource_type='system', detail='Furnivo demo records were initialized.'))
        db.session.commit()


def seed_schedules():
    if db.session.scalar(db.select(DeliverySchedule).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if order and admin:
        db.session.add(DeliverySchedule(order_id=order.id, schedule_type='Delivery', scheduled_date=__import__('datetime').date(2026, 10, 18), time_slot='10:00–12:00', assigned_team='North Delhi delivery team', status='Scheduled', created_by_id=admin.id))
        db.session.add(DeliverySchedule(order_id=order.id, schedule_type='Installation', scheduled_date=__import__('datetime').date(2026, 10, 20), time_slot='09:00–13:00', assigned_team='Furnivo installation team', status='Scheduled', created_by_id=admin.id))
        db.session.commit()


def seed_warehouses():
    if db.session.scalar(db.select(Warehouse).limit(1)):
        return
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    products = db.session.scalars(db.select(Product).order_by(Product.id)).all()
    delhi = Warehouse(name='Delhi warehouse', address='Okhla Phase II, New Delhi', manager='Ravi Kumar')
    gurugram = Warehouse(name='Gurugram warehouse', address='Sector 18, Gurugram', manager='Nisha Verma')
    db.session.add_all([delhi, gurugram]); db.session.flush()
    if products:
        db.session.add(WarehouseStock(warehouse_id=delhi.id, product_id=products[0].id, quantity=8, reserved_quantity=1))
        if len(products) > 1: db.session.add(WarehouseStock(warehouse_id=delhi.id, product_id=products[1].id, quantity=20, reserved_quantity=4))
        if len(products) > 2: db.session.add(WarehouseStock(warehouse_id=gurugram.id, product_id=products[2].id, quantity=900, reserved_quantity=200))
        db.session.commit()


def seed_returns():
    if db.session.scalar(db.select(ReturnRequest).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    invoice = db.session.scalar(db.select(Invoice).where(Invoice.invoice_number == 'INV-2001'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if order and invoice and admin:
        item = ReturnRequest(order_id=order.id, invoice_id=invoice.id, customer_name=order.customer_name, reason='One light fixture arrived damaged', amount=12400, status='Requested', created_by_id=admin.id)
        db.session.add(item); db.session.commit()


def seed_configurator():
    if not db.session.scalar(db.select(QuotePreset).limit(1)):
        admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
        sofa = db.session.scalar(db.select(Product).where(Product.sku == 'FUR-SOF-101'))
        light = db.session.scalar(db.select(Product).where(Product.sku == 'INT-LGT-204'))
        panel = db.session.scalar(db.select(Product).where(Product.sku == 'BLD-PNL-310'))
        if admin and sofa and light and panel:
            import json
            db.session.add_all([
                QuotePreset(name='Living room starter', kind='Room package', room='Living room', description='Sofa and statement lighting package for a complete living room refresh.', discount_percent=5, items_json=json.dumps([
                    {'product_id': sofa.id, 'description': sofa.name, 'sku': sofa.sku, 'quantity': 1, 'unit': sofa.unit, 'unit_price': float(sofa.price)},
                    {'product_id': light.id, 'description': light.name, 'sku': light.sku, 'quantity': 2, 'unit': light.unit, 'unit_price': float(light.price)},
                ]), created_by_id=admin.id),
                QuotePreset(name='Complete office package', kind='Bundle', room='Office', description='A practical package combining modular seating, lighting and acoustic wall finish.', discount_percent=8, items_json=json.dumps([
                    {'product_id': sofa.id, 'description': sofa.name, 'sku': sofa.sku, 'quantity': 2, 'unit': sofa.unit, 'unit_price': float(sofa.price)},
                    {'product_id': light.id, 'description': light.name, 'sku': light.sku, 'quantity': 4, 'unit': light.unit, 'unit_price': float(light.price)},
                    {'product_id': panel.id, 'description': panel.name, 'sku': panel.sku, 'quantity': 120, 'unit': panel.unit, 'unit_price': float(panel.price)},
                ]), created_by_id=admin.id),
            ])
            db.session.commit()
    customer = db.session.scalar(db.select(Customer).where(Customer.company == 'Northline Studio'))
    if customer and not db.session.scalar(db.select(CustomerPricing).where(CustomerPricing.customer_id == customer.id)):
        db.session.add(CustomerPricing(customer_id=customer.id, tier='Gold', discount_percent=10))
        db.session.commit()


def seed_production():
    if db.session.scalar(db.select(ProductionJob).limit(1)):
        return
    order = db.session.scalar(db.select(Order).where(Order.order_number == 'ORD-1001'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    sofa = db.session.scalar(db.select(Product).where(Product.sku == 'FUR-SOF-101'))
    light = db.session.scalar(db.select(Product).where(Product.sku == 'INT-LGT-204'))
    if order and admin and sofa and light:
        job = ProductionJob(order_id=order.id, job_number='JOB-5001', status='Assembly', scheduled_start=__import__('datetime').date(2026, 9, 24), due_date=__import__('datetime').date(2026, 10, 10), assigned_team='North workshop team', wastage_percent=5, notes='Demo job card generated from approved quote.', created_by_id=admin.id)
        job.bom_items = [BomItem(product_id=sofa.id, description='Aster Modular Sofa', quantity=2, unit=sofa.unit, wastage_percent=5), BomItem(product_id=light.id, description='Halo Pendant Light', quantity=2, unit=light.unit, wastage_percent=3)]
        db.session.add(job)
        db.session.commit()


def seed_reconciliation():
    if db.session.scalar(db.select(PaymentReconciliation).limit(1)):
        return
    invoice = db.session.scalar(db.select(Invoice).where(Invoice.invoice_number == 'INV-2001'))
    if invoice:
        db.session.add(PaymentReconciliation(invoice_id=invoice.id, provider='Bank transfer', external_id='NEFT-001', amount=50000, status='Paid'))
        db.session.commit()


def seed_contracts():
    if db.session.scalar(db.select(Contract).limit(1)):
        return
    quote = db.session.scalar(db.select(Quote).where(Quote.quote_number == 'Q-1042'))
    admin = db.session.scalar(db.select(User).where(User.email == 'admin@furnivo.demo'))
    if quote and admin:
        db.session.add(Contract(contract_number='CTR-7001', quote_id=quote.id, title='Northline Studio project agreement', terms='1. Furnivo will deliver the approved scope and materials listed in the quotation.\n2. Production begins after written approval and agreed advance payment.\n3. Delivery and installation dates are scheduled after material confirmation.\n4. Variations require written approval and may change price or timeline.', status='Sent', created_by_id=admin.id))
        db.session.commit()


def seed_gst():
    if db.session.scalar(db.select(EInvoice).limit(1)):
        return
    invoice = db.session.scalar(db.select(Invoice).where(Invoice.invoice_number == 'INV-2001'))
    if invoice:
        db.session.add(EInvoice(invoice_id=invoice.id, gstin=invoice.customer.gstin if invoice.customer else '', place_of_supply='Delhi', tax_mode='CGST/SGST', hsn_summary_json='[{"hsn":"9403","description":"Furniture and interiors","taxable_value":158000}]', cgst_amount=14220, sgst_amount=14220, irn='DEMO-INV-2001-IRN', acknowledgement_number='ACK-DEMO-2001', status='Generated'))
        db.session.commit()
