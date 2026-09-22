export const demoUsers = [
  { id: 1, name: 'Aarav Admin', email: 'admin@furnivo.demo', password: 'admin123', role: 'admin' },
  { id: 2, name: 'Meera Sales', email: 'sales@furnivo.demo', password: 'sales123', role: 'sales' },
  { id: 3, name: 'Kabir Designer', email: 'designer@furnivo.demo', password: 'design123', role: 'designer' },
  { id: 4, name: 'Riya Client', email: 'client@furnivo.demo', password: 'client123', role: 'client' },
]

export const demoAccessUsers = demoUsers.map((user) => ({
  user,
  permissions: user.role === 'admin'
    ? [{ id: 1, permission: '*', scope: 'global', is_enabled: true }]
    : [{ id: 2, permission: user.role === 'sales' ? 'quotes.discount' : 'portal.view', scope: user.role === 'sales' ? 'approval' : 'own', is_enabled: true }],
  departments: user.role === 'admin' ? [{ department: 'Operations', role_title: 'Administrator' }] : [{ department: user.role === 'sales' ? 'Sales' : user.role === 'designer' ? 'Design' : 'Client', role_title: user.role }],
}))

export const demoDepartments = [
  { id: 1, name: 'Sales', description: 'Quotations and customer relationships.' },
  { id: 2, name: 'Design', description: 'Design delivery and specifications.' },
  { id: 3, name: 'Operations', description: 'Production, delivery, and service.' },
]

export const demoApprovalRequests = [
  { id: 1, request_type: 'Discount', resource_type: 'quote', resource_id: 'Q-1042', amount: 186400, detail: 'Approval required for a customer discount above the sales threshold.', status: 'Requested', requested_by: demoUsers[1], approved_by: null, created_at: '2026-09-18T10:00:00Z', updated_at: '2026-09-18T10:00:00Z' },
]

export const demoProjectOwnership = [
  { id: 1, order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', user_id: 2, owner: demoUsers[1], assigned_by: 'Aarav Admin' },
]

export const demoProducts = [
  {
    id: 1,
    sku: 'FUR-SOF-101',
    name: 'Aster Modular Sofa',
    category: 'Furniture',
    price: 78500,
    unit: 'set',
    material: 'Oak frame, performance fabric',
    image: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=80',
    variants: [
      { id: 101, sku: 'FUR-SOF-101-SAND', finish: 'Sand Boucle', dimensions: '2600 × 780 × 980 mm', price_delta: 0, stock_status: 'Made to order' },
      { id: 102, sku: 'FUR-SOF-101-OLIVE', finish: 'Olive Performance', dimensions: '2600 × 780 × 980 mm', price_delta: 4500, stock_status: 'Made to order' },
    ],
  },
  {
    id: 2,
    sku: 'INT-LGT-204',
    name: 'Halo Pendant Light',
    category: 'Interiors',
    price: 12400,
    unit: 'piece',
    material: 'Powder-coated metal, frosted glass',
    image: 'https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 3,
    sku: 'BLD-PNL-310',
    name: 'Terra Fluted Wall Panel',
    category: 'Building Material',
    price: 920,
    unit: 'sq.ft',
    material: 'WPC acoustic panel',
    image: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 4,
    sku: 'FUR-TBL-118',
    name: 'Moro Dining Table',
    category: 'Furniture',
    price: 56900,
    unit: 'piece',
    material: 'Solid ash wood, stone top',
    image: 'https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 5,
    sku: 'INT-CHR-220',
    name: 'Noma Lounge Chair',
    category: 'Interiors',
    price: 28600,
    unit: 'piece',
    material: 'Boucle upholstery, walnut legs',
    image: 'https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 6,
    sku: 'BLD-TIL-322',
    name: 'Lime Stone Surface',
    category: 'Building Material',
    price: 460,
    unit: 'sq.ft',
    material: 'Low-sheen mineral composite',
    image: 'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?auto=format&fit=crop&w=900&q=80',
  },
]

export const demoQuotes = [
  {
    id: 'Q-1042',
    customer: 'Northline Studio',
    amount: 186400,
    status: 'Sent',
    date: '2026-09-18',
  },
  {
    id: 'Q-1041',
    customer: 'The Green House',
    amount: 94200,
    status: 'Draft',
    date: '2026-09-17',
  },
  {
    id: 'Q-1038',
    customer: 'Avenue Architects',
    amount: 328500,
    status: 'Approved',
    date: '2026-09-12',
  },
]

export const demoLeads = [
  {
    id: 1,
    name: 'Sana Kapoor',
    company: 'SK Atelier',
    phone: '+91 98111 22334',
    source: 'Website',
    stage: 'New',
    value: 240000,
  },
  {
    id: 2,
    name: 'Arjun Mehta',
    company: 'Mehta Homes',
    phone: '+91 98770 11228',
    source: 'Referral',
    stage: 'Qualified',
    value: 510000,
  },
  {
    id: 3,
    name: 'Devika Rao',
    company: 'Form & Field',
    phone: '+91 98990 33001',
    source: 'Instagram',
    stage: 'Proposal',
    value: 175000,
  },
  {
    id: 4,
    name: 'Neil Thomas',
    company: 'NTH Build',
    phone: '+91 97110 81020',
    source: 'Exhibition',
    stage: 'Won',
    value: 690000,
  },
]


export const demoCustomers = [
  { id: 1, company: 'Northline Studio', contact_name: 'Ishita Arora', email: 'projects@northline.demo', phone: '+91 98100 21001', billing_address: 'New Delhi', project_address: 'Defence Colony, New Delhi', gstin: '07DEMO1234A1Z5', notes: '' },
  { id: 2, company: 'The Green House', contact_name: 'Rohan Sen', email: 'hello@greenhouse.demo', phone: '+91 98100 21002', billing_address: 'Gurugram', project_address: 'Gurugram, Haryana', gstin: '', notes: '' },
  { id: 3, company: 'Avenue Architects', contact_name: 'Neha Jain', email: 'studio@avenue.demo', phone: '+91 98100 21003', billing_address: 'Noida', project_address: 'Noida, Uttar Pradesh', gstin: '', notes: '' },
]

export const demoOrders = [
  { id: 1, order_number: 'ORD-1001', quote_id: 1042, quote_number: 'Q-1042', customer: 'Northline Studio', status: 'Confirmed', production_status: 'In production', delivery_date: '2026-10-18', installation_status: 'Scheduled', amount: 186400, notes: 'Demo project order', updates: [{ id: 1, body: 'Materials confirmed and production slot reserved.', author: 'Aarav Admin', created_at: '2026-09-18T10:00:00.000Z' }] },
]

export const demoInventory = [
  { id: 1, product_id: 1, product: 'Aster Modular Sofa', sku: 'FUR-SOF-101', quantity: 12, reserved_quantity: 2, available_quantity: 10, reorder_level: 4, is_low_stock: false, supplier: 'Oak & Co. Furnishings', location: 'Delhi warehouse' },
  { id: 2, product_id: 2, product: 'Halo Pendant Light', sku: 'INT-LGT-204', quantity: 24, reserved_quantity: 5, available_quantity: 19, reorder_level: 8, is_low_stock: false, supplier: 'Halo Lighting Works', location: 'Delhi warehouse' },
  { id: 3, product_id: 3, product: 'Terra Fluted Wall Panel', sku: 'BLD-PNL-310', quantity: 1200, reserved_quantity: 300, available_quantity: 900, reorder_level: 400, is_low_stock: false, supplier: 'Terra Surfaces', location: 'Gurugram warehouse' },
]

export const demoNotifications = [
  { id: 1, user_id: 1, type: 'task', title: 'Follow-up workspace ready', body: 'Review the active lead pipeline and open tasks.', related_type: 'lead', related_id: '', is_read: false, created_at: '2026-09-22T08:30:00.000Z' },
  { id: 2, user_id: 4, type: 'quote', title: 'Quotation ready for review', body: 'Q-1042 is ready in your client portal.', related_type: 'quote', related_id: '1', is_read: false, created_at: '2026-09-22T08:30:00.000Z' },
]

export const demoInvoices = [
  { id: 1, invoice_number: 'INV-2001', order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', issue_date: '2026-09-18', due_date: '2026-10-03', status: 'Partially Paid', subtotal: 158000, tax_amount: 28440, total: 186440, amount_paid: 50000, balance: 136440, payment_link: '/pay/INV-2001', payments: [{ id: 1, amount: 50000, method: 'Bank transfer', reference: 'NEFT-001', paid_at: '2026-09-19T10:00:00.000Z' }] },
]

export const demoSuppliers = [{ id: 1, name: 'Oak & Co. Furnishings', email: 'orders@oakco.demo', phone: '+91 98000 10001', notes: 'Primary timber and furniture supplier' }]
export const demoPurchaseOrders = [{ id: 1, po_number: 'PO-3001', supplier_id: 1, supplier: 'Oak & Co. Furnishings', status: 'Confirmed', order_date: '2026-09-19', expected_date: '2026-10-05', total: 260000, items: [{ id: 1, product_id: 1, description: 'Aster Modular Sofa', quantity: 4, unit_cost: 65000, line_total: 260000 }] }]

export const demoAuditLogs = [{ id: 1, user: { name: 'Aarav Admin', email: 'admin@furnivo.demo', role: 'admin' }, action: 'Seeded demo workspace', resource_type: 'system', resource_id: '', detail: 'Furnivo demo records were initialized.', created_at: '2026-09-22T08:30:00.000Z' }]
export const demoSchedules = [{ id: 1, order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', schedule_type: 'Delivery', scheduled_date: '2026-10-18', time_slot: '10:00–12:00', assigned_team: 'North Delhi delivery team', status: 'Scheduled', proof_url: '', notes: '' }, { id: 2, order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', schedule_type: 'Installation', scheduled_date: '2026-10-20', time_slot: '09:00–13:00', assigned_team: 'Furnivo installation team', status: 'Scheduled', proof_url: '', notes: '' }]
export const demoWarehouses = [{ id: 1, name: 'Delhi warehouse', address: 'Okhla Phase II, New Delhi', manager: 'Ravi Kumar' }, { id: 2, name: 'Gurugram warehouse', address: 'Sector 18, Gurugram', manager: 'Nisha Verma' }]
export const demoWarehouseStock = [{ id: 1, warehouse_id: 1, warehouse: 'Delhi warehouse', product_id: 1, product: 'Aster Modular Sofa', sku: 'FUR-SOF-101', quantity: 8, reserved_quantity: 1, available_quantity: 7 }, { id: 2, warehouse_id: 1, warehouse: 'Delhi warehouse', product_id: 2, product: 'Halo Pendant Light', sku: 'INT-LGT-204', quantity: 20, reserved_quantity: 4, available_quantity: 16 }, { id: 3, warehouse_id: 2, warehouse: 'Gurugram warehouse', product_id: 3, product: 'Terra Fluted Wall Panel', sku: 'BLD-PNL-310', quantity: 900, reserved_quantity: 200, available_quantity: 700 }]
export const demoStockMovements = []
export const demoReturns = [{ id: 1, order_id: 1, order_number: 'ORD-1001', invoice_id: 1, customer: 'Northline Studio', reason: 'One light fixture arrived damaged', amount: 12400, status: 'Requested', notes: '', credit_note: null, created_at: '2026-09-21T10:00:00.000Z' }]
export const demoQuotePresets = [
  { id: 1, name: 'Living room starter', kind: 'Room package', room: 'Living room', description: 'Sofa and statement lighting package for a complete living room refresh.', discount_percent: 5, items: [{ product_id: 1, description: 'Aster Modular Sofa', sku: 'FUR-SOF-101', quantity: 1, unit: 'set', unit_price: 78500 }, { product_id: 2, description: 'Halo Pendant Light', sku: 'INT-LGT-204', quantity: 2, unit: 'piece', unit_price: 12400 }] },
  { id: 2, name: 'Complete office package', kind: 'Bundle', room: 'Office', description: 'A practical package combining modular seating, lighting and acoustic wall finish.', discount_percent: 8, items: [{ product_id: 1, description: 'Aster Modular Sofa', sku: 'FUR-SOF-101', quantity: 2, unit: 'set', unit_price: 78500 }, { product_id: 2, description: 'Halo Pendant Light', sku: 'INT-LGT-204', quantity: 4, unit: 'piece', unit_price: 12400 }, { product_id: 3, description: 'Terra Fluted Wall Panel', sku: 'BLD-PNL-310', quantity: 120, unit: 'sq.ft', unit_price: 920 }] },
]
export const demoCustomerPricing = [{ id: 1, customer_id: 1, customer: 'Northline Studio', tier: 'Gold', discount_percent: 10 }]
export const demoProductionJobs = [{ id: 1, job_number: 'JOB-5001', order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', status: 'Assembly', scheduled_start: '2026-09-24', due_date: '2026-10-10', assigned_team: 'North workshop team', wastage_percent: 5, notes: 'Demo job card generated from approved quote.', bom_items: [{ id: 1, product_id: 1, product: 'Aster Modular Sofa', description: 'Aster Modular Sofa', quantity: 2, unit: 'set', wastage_percent: 5, planned_quantity: 2.1, status: 'Required' }, { id: 2, product_id: 2, product: 'Halo Pendant Light', description: 'Halo Pendant Light', quantity: 2, unit: 'piece', wastage_percent: 3, planned_quantity: 2.06, status: 'Required' }] }]
export const demoPaymentReconciliations = [{ id: 1, invoice_id: 1, invoice_number: 'INV-2001', customer: 'Northline Studio', provider: 'Bank transfer', external_id: 'NEFT-001', amount: 50000, refunded_amount: 0, refundable_amount: 50000, status: 'Paid', refund_status: 'Not refunded', provider_refund_id: '', dispute_reason: '', created_at: '2026-09-19T10:00:00.000Z' }]
export const demoContracts = [{ id: 1, contract_number: 'CTR-7001', quote_id: 1, quote_number: 'Q-1042', customer: 'Northline Studio', title: 'Northline Studio project agreement', terms: '1. Furnivo will deliver the approved scope and materials listed in the quotation.\n2. Production begins after written approval and agreed advance payment.\n3. Delivery and installation dates are scheduled after material confirmation.', status: 'Sent', locked: false, signed_at: null, signatures: [] }]
export const demoSupportTickets = [{ id: 1, order_id: 1, order_number: 'ORD-1001', subject: 'Confirm installation access', message: 'Please confirm the installation team arrival window.', status: 'Open', response: '', created_at: '2026-09-21T11:00:00.000Z', updated_at: '2026-09-21T11:00:00.000Z' }]
export const demoWarranties = [{ id: 1, warranty_number: 'WAR-7001', order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', product_id: 1, product: 'Aster Modular Sofa', start_date: '2026-10-20', end_date: '2028-10-19', coverage: 'Manufacturing defects, hardware, and installation issues', status: 'Active', serial_number: 'AST-1001' }]
export const demoServiceTickets = [{ id: 1, ticket_number: 'SVC-8001', warranty_id: 1, warranty_number: 'WAR-7001', order_id: 1, order_number: 'ORD-1001', customer: 'Northline Studio', subject: 'Post-installation alignment check', description: 'Customer requested a technician visit to verify the sofa modules after installation.', priority: 'High', status: 'Assigned', assigned_to_id: 2, assigned_to: demoUsers[1], sla_due: '2026-10-24', resolution: '', created_at: '2026-10-21T11:00:00.000Z', updated_at: '2026-10-21T11:00:00.000Z' }]
export const demoAnalytics = { summary: { revenue: 50000, invoice_total: 186440, outstanding: 136440, quote_pipeline: 514900, conversion_rate: 33.3, lead_win_rate: 25, inventory_value: 1877200, low_stock: 0 }, quotes_by_status: [{ label: 'Sent', count: 1 }, { label: 'Draft', count: 1 }, { label: 'Approved', count: 1 }], leads_by_stage: [{ label: 'New', count: 1 }, { label: 'Qualified', count: 1 }, { label: 'Proposal', count: 1 }, { label: 'Won', count: 1 }], production_by_status: [{ label: 'Assembly', count: 1 }], forecast: { next_30_days: 230215, next_90_days: 436175, method: 'Collected revenue plus weighted open pipeline' }, top_customers: [{ customer: 'Northline Studio', value: 186440 }] }
export const demoOpsHealth = { status: 'ok', version: 'furnivo-v3', environment: 'demo', database: 'demo-local', payment_provider: 'demo', auto_seed: true, rate_limit_per_minute: 120 }
export const demoBackups = []
export const demoEInvoices = [{ id: 1, invoice_id: 1, invoice_number: 'INV-2001', customer: 'Northline Studio', gstin: '07DEMO1234A1Z5', place_of_supply: 'Delhi', tax_mode: 'CGST/SGST', hsn_summary: [{ hsn: '9403', description: 'Furniture and interiors', taxable_value: 158000 }], cgst_amount: 14220, sgst_amount: 14220, igst_amount: 0, irn: 'DEMO-INV-2001-IRN', acknowledgement_number: 'ACK-DEMO-2001', status: 'Generated', eway_bill_number: '', created_at: '2026-09-18T12:00:00.000Z' }]
export const demoBackgroundJobs = []
