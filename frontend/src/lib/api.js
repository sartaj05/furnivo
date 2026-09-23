import { demoAccessUsers, demoAnalytics, demoApprovalRequests, demoAuditLogs, demoBackups, demoBackgroundJobs, demoContracts, demoCustomerPricing, demoCustomers, demoDepartments, demoEInvoices, demoFieldVisits, demoFurnitureConfigurations, demoIntegrations, demoInventory, demoInvoices, demoLeads, demoNotifications, demoOpsHealth, demoOrders, demoPaymentReconciliations, demoProducts, demoProductionJobs, demoProjectOwnership, demoPurchaseOrders, demoQuotePresets, demoQuotes, demoReturns, demoSchedules, demoServiceTickets, demoStockMovements, demoSupportTickets, demoSuppliers, demoSyncRuns, demoUsers, demoWarehouseStock, demoWarehouses, demoWarranties } from '../data/demoData'

const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, '')
const STORAGE_KEY = 'furnivo-demo-db'
const REQUEST_TIMEOUT_MS = 8000

const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms))

function addDemoQuoteRevision(quote, action, comment = '') {
  const history = quote.history || []
  return {
    ...quote,
    history: [{
      id: Date.now(),
      version: history.length + 1,
      action,
      status: quote.status,
      subtotal: Number(quote.subtotal || 0),
      amount: Number(quote.amount || 0),
      comment,
      created_at: new Date().toISOString(),
    }, ...history],
  }
}

function addDemoNotification(db, userId, title, body, type = 'info', relatedType = '', relatedId = '') {
  db.notifications = [{ id: Date.now(), user_id: userId, type, title, body, related_type: relatedType, related_id: String(relatedId || ''), is_read: false, created_at: new Date().toISOString() }, ...(db.notifications || [])]
}

function setDataMode(mode) {
  localStorage.setItem('furnivo-mode', mode)
  window.dispatchEvent(new CustomEvent('furnivo-mode-change', { detail: mode }))
}

function getLocalDb() {
  const existing = localStorage.getItem(STORAGE_KEY)
  if (existing) {
    let parsed
    try {
      parsed = JSON.parse(existing)
    } catch {
      parsed = null
    }
    if (!parsed || typeof parsed !== 'object') {
      localStorage.removeItem(STORAGE_KEY)
      return getLocalDb()
    }
    const normalized = {
      products: parsed.products || demoProducts,
      quotes: parsed.quotes || demoQuotes,
      leads: parsed.leads || demoLeads,
      users: parsed.users || demoUsers,
      customers: parsed.customers || demoCustomers,
      orders: parsed.orders || demoOrders,
      inventory: parsed.inventory || demoInventory,
      notifications: parsed.notifications || demoNotifications,
      invoices: parsed.invoices || demoInvoices,
      suppliers: parsed.suppliers || demoSuppliers,
      purchaseOrders: parsed.purchaseOrders || demoPurchaseOrders,
      auditLogs: parsed.auditLogs || demoAuditLogs,
      schedules: parsed.schedules || demoSchedules,
      warehouses: parsed.warehouses || demoWarehouses,
      warehouseStock: parsed.warehouseStock || demoWarehouseStock,
      stockMovements: parsed.stockMovements || demoStockMovements,
      returns: parsed.returns || demoReturns,
      quotePresets: parsed.quotePresets || demoQuotePresets,
      customerPricing: parsed.customerPricing || demoCustomerPricing,
      productionJobs: parsed.productionJobs || demoProductionJobs,
      paymentReconciliations: parsed.paymentReconciliations || demoPaymentReconciliations,
      contracts: parsed.contracts || demoContracts,
      supportTickets: parsed.supportTickets || demoSupportTickets,
      backups: parsed.backups || demoBackups,
      eInvoices: parsed.eInvoices || demoEInvoices,
      backgroundJobs: parsed.backgroundJobs || demoBackgroundJobs,
      accessUsers: parsed.accessUsers || demoAccessUsers,
      departments: parsed.departments || demoDepartments,
      approvals: parsed.approvals || demoApprovalRequests,
      projectOwnership: parsed.projectOwnership || demoProjectOwnership,
      warranties: parsed.warranties || demoWarranties,
      serviceTickets: parsed.serviceTickets || demoServiceTickets,
      integrations: parsed.integrations || demoIntegrations,
      syncRuns: parsed.syncRuns || demoSyncRuns,
      fieldVisits: parsed.fieldVisits || demoFieldVisits,
      furnitureConfigurations: parsed.furnitureConfigurations || demoFurnitureConfigurations,
    }
    if (!parsed.users) localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized))
    return normalized
  }

  const initial = {
    products: demoProducts,
    quotes: demoQuotes,
    leads: demoLeads,
    users: demoUsers,
    customers: demoCustomers,
    orders: demoOrders,
    inventory: demoInventory,
    notifications: demoNotifications,
    invoices: demoInvoices,
    suppliers: demoSuppliers,
    purchaseOrders: demoPurchaseOrders,
    auditLogs: demoAuditLogs,
    schedules: demoSchedules,
    warehouses: demoWarehouses,
    warehouseStock: demoWarehouseStock,
    stockMovements: demoStockMovements,
    returns: demoReturns,
    quotePresets: demoQuotePresets,
    customerPricing: demoCustomerPricing,
    productionJobs: demoProductionJobs,
    paymentReconciliations: demoPaymentReconciliations,
    contracts: demoContracts,
    supportTickets: demoSupportTickets,
    backups: demoBackups,
    eInvoices: demoEInvoices,
    backgroundJobs: demoBackgroundJobs,
    accessUsers: demoAccessUsers,
    departments: demoDepartments,
    approvals: demoApprovalRequests,
    projectOwnership: demoProjectOwnership,
    warranties: demoWarranties,
    serviceTickets: demoServiceTickets,
    integrations: demoIntegrations,
    syncRuns: demoSyncRuns,
    fieldVisits: demoFieldVisits,
    furnitureConfigurations: demoFurnitureConfigurations,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(initial))
  return initial
}

function saveLocalDb(db) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db))
}

async function backendRequest(path, options = {}) {
  if (!API_URL) throw new Error('Backend URL not configured')

  const token = localStorage.getItem('furnivo-token')
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    })
  } catch (error) {
    // A network failure means the demo adapter is the correct source of data.
    setDataMode('demo')
    throw error
  } finally {
    window.clearTimeout(timeout)
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(data.message || `API request failed: ${response.status}`)
    error.status = response.status
    throw error
  }
  setDataMode('api')
  return data
}

export async function login(email, password) {
  try {
    return await backendRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  } catch (apiError) {
    if (apiError.status) throw apiError
    await delay()
    const db = getLocalDb()
    const user = db.users.find(
      (item) => item.email.toLowerCase() === email.toLowerCase() && item.password === password,
    )
    if (!user) throw new Error('Invalid email or password')

    return {
      token: `demo-token-${user.id}`,
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
      mode: 'demo',
    }
  }
}

export async function verifyMfa(challengeId, code) {
  try { return await backendRequest('/auth/mfa/verify', { method: 'POST', body: JSON.stringify({ challenge_id: challengeId, code }) }) }
  catch (error) { if (error.status) throw error; throw new Error('MFA verification requires the connected backend.') }
}

export async function refreshSession() {
  return backendRequest('/auth/refresh', { method: 'POST', body: JSON.stringify({}) })
}

export async function logoutSession() {
  try { return await backendRequest('/auth/logout', { method: 'POST', body: JSON.stringify({}) }) } catch (error) { if (error.status) throw error; return { ok: true, mode: 'demo' } }
}

export async function getSecurityStatus() {
  try { return await backendRequest('/auth/security') }
  catch (error) { if (error.status) throw error; await delay(); return { mfa_enabled: false, mfa_method: null, sessions: [], mode: 'demo' } }
}

export async function enableMfa() {
  try { return await backendRequest('/auth/mfa/enable', { method: 'POST', body: JSON.stringify({}) }) }
  catch (error) { if (error.status) throw error; return { enabled: true, method: 'demo-otp', message: 'Demo MFA enabled. Connect the backend for real login challenges.', mode: 'demo' } }
}

export async function disableMfa() {
  try { return await backendRequest('/auth/mfa/disable', { method: 'POST', body: JSON.stringify({}) }) }
  catch (error) { if (error.status) throw error; return { enabled: false, mode: 'demo' } }
}

export async function revokeAllSessions() {
  try { return await backendRequest('/auth/sessions/revoke-all', { method: 'POST', body: JSON.stringify({}) }) }
  catch (error) { if (error.status) throw error; return { ok: true, mode: 'demo' } }
}

export async function register(name, email, password) {
  try {
    return await backendRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
  } catch (apiError) {
    if (apiError.status) throw apiError
    await delay()
    const db = getLocalDb()
    const normalizedEmail = email.trim().toLowerCase()

    if (db.users.some((item) => item.email.toLowerCase() === normalizedEmail)) {
      throw new Error('An account with this email already exists.')
    }

    const user = {
      id: Math.max(0, ...db.users.map((item) => Number(item.id) || 0)) + 1,
      name: name.trim(),
      email: normalizedEmail,
      password,
      role: 'client',
    }

    db.users.push(user)
    saveLocalDb(db)

    return {
      token: `demo-token-${user.id}`,
      user: { id: user.id, name: user.name, email: user.email, role: user.role },
      mode: 'demo',
    }
  }
}

export async function getProducts(options = {}) {
  const query = new URLSearchParams(Object.entries(options).filter(([, value]) => value !== undefined && value !== ''))
  try {
    return await backendRequest(`/products${query.toString() ? `?${query}` : ''}`)
  } catch (error) {
    if (error.status) throw error
    await delay()
    const all = getLocalDb().products.filter((item) => options.include_archived === 'true' || item.is_active !== false).filter((item) => !options.q || `${item.name} ${item.sku} ${item.material}`.toLowerCase().includes(String(options.q).toLowerCase()))
    return { items: all, pagination: { page: 1, page_size: all.length, total: all.length, pages: 1 }, mode: 'demo' }
  }
}

const demoConfigurationOptions = {
  materials: [{ value: 'Oak', label: 'Oak', price_delta: 0 }, { value: 'Ash', label: 'Ash', price_delta: 2800 }, { value: 'Walnut', label: 'Walnut', price_delta: 6500 }, { value: 'Engineered wood', label: 'Engineered wood', price_delta: -1800 }],
  fabrics: [{ value: 'Performance fabric', label: 'Performance fabric', price_delta: 0 }, { value: 'Sand boucle', label: 'Sand boucle', price_delta: 3200 }, { value: 'Velvet', label: 'Velvet', price_delta: 4200 }, { value: 'Leather', label: 'Leather', price_delta: 9800 }],
  colors: [{ value: 'Natural', label: 'Natural', price_delta: 0, swatch: '#c7ab83' }, { value: 'Sage', label: 'Sage', price_delta: 900, swatch: '#879b87' }, { value: 'Terracotta', label: 'Terracotta', price_delta: 1200, swatch: '#bd745b' }, { value: 'Charcoal', label: 'Charcoal', price_delta: 1500, swatch: '#454946' }],
  finishes: [{ value: 'Matte', label: 'Matte', price_delta: 0 }, { value: 'Natural oil', label: 'Natural oil', price_delta: 1800 }, { value: 'High gloss', label: 'High gloss', price_delta: 2600 }],
  dimension_surcharge_percent: 8,
}

export async function getFurnitureConfigurationOptions() {
  try { return await backendRequest('/quote-config/options') }
  catch (error) {
    if (error.status) throw error
    await delay()
    return { options: demoConfigurationOptions, mode: 'demo' }
  }
}

export async function getFurnitureConfigurations() {
  try { return await backendRequest('/quote-config/configurations') }
  catch (error) {
    if (error.status) throw error
    await delay()
    return { items: getLocalDb().furnitureConfigurations, mode: 'demo' }
  }
}

export async function saveFurnitureConfiguration(payload) {
  try { return await backendRequest('/quote-config/configurations', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const items = (payload.items || []).map((item) => ({
      ...item,
      line_total: Number(item.quantity || 0) * Number(item.unit_price || 0),
    }))
    const item = {
      id: Math.max(0, ...db.furnitureConfigurations.map((configuration) => Number(configuration.id) || 0)) + 1,
      configuration_number: `CFG-${2000 + db.furnitureConfigurations.length + 1}`,
      name: payload.name,
      room: payload.room || '',
      customer_id: payload.customer_id || null,
      customer: db.customers.find((customer) => Number(customer.id) === Number(payload.customer_id))?.company || null,
      quote_id: null,
      status: 'Saved',
      items,
      subtotal: items.reduce((sum, line) => sum + Number(line.line_total || 0), 0),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    db.furnitureConfigurations = [item, ...db.furnitureConfigurations]
    saveLocalDb(db)
    return { item, mode: 'demo' }
  }
}

export async function getQuotes() {
  try {
    return await backendRequest('/quotes')
  } catch (error) {
    if (error.status) throw error
    await delay()
    return { items: getLocalDb().quotes, mode: 'demo' }
  }
}

export async function getClientQuotes() {
  try {
    return await backendRequest('/quotes/client')
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    return {
      items: db.quotes.map((quote) => ({ ...quote, client_access: quote.client_access || { last_action: quote.status === 'Approved' ? 'Approved' : 'Pending', response_comment: '' } })),
      mode: 'demo',
    }
  }
}

export async function getQuoteHistory(id) {
  try {
    return await backendRequest(`/quotes/${id}/history`)
  } catch (error) {
    if (error.status) throw error
    await delay()
    const quote = getLocalDb().quotes.find((item) => item.database_id === id || item.id === id)
    return {
      items: quote?.history || [{ id: `${id}-1`, version: 1, action: 'Created', status: quote?.status || 'Draft', amount: quote?.amount || 0, subtotal: quote?.subtotal || quote?.amount || 0, comment: '', created_at: quote?.date }],
      mode: 'demo',
    }
  }
}

export async function respondToQuote(id, action, comment = '') {
  try {
    return await backendRequest(`/quotes/${id}/client-response`, { method: 'POST', body: JSON.stringify({ action, comment }) })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    let automation = { contract: null, contract_created: false }
    const selectedQuote = db.quotes.find((quote) => quote.database_id === id || quote.id === id)
    if (action === 'Approved' && selectedQuote) {
      let contract = db.contracts.find((item) => Number(item.quote_id) === Number(selectedQuote.database_id || selectedQuote.id))
      if (!contract) {
        contract = { id: Date.now(), contract_number: `CTR-${7000 + db.contracts.length + 1}`, quote_id: selectedQuote.database_id || selectedQuote.id, quote_number: selectedQuote.id, customer: selectedQuote.customer, title: `${selectedQuote.id} - project agreement`, terms: '1. Furnivo will deliver the approved scope and materials listed in the quotation.\n2. Production begins after written approval and the agreed advance payment.\n3. Delivery and installation dates are scheduled after material confirmation.', status: 'Sent', locked: false, signatures: [] }
        db.contracts = [contract, ...db.contracts]
        automation = { contract, contract_created: true }
      } else automation.contract = contract
    }
    db.quotes = db.quotes.map((quote) => quote.database_id === id || quote.id === id
      ? addDemoQuoteRevision({ ...quote, status: action, client_access: { ...(quote.client_access || {}), last_action: action, response_comment: comment } }, `Client ${action}`, comment)
      : quote)
    addDemoNotification(db, 1, 'Client response received', `${id}: ${action}.`, 'quote', 'quote', id)
    saveLocalDb(db)
    return { item: db.quotes.find((quote) => quote.database_id === id || quote.id === id), automation, mode: 'demo' }
  }
}

export async function createQuote(payload) {
  try {
    return await backendRequest('/quotes', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const subtotal = (payload.items || []).reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0)
    const discountPercent = Number(payload.discount_percent || 0)
    const discountAmount = subtotal * discountPercent / 100
    const taxPercent = Number(payload.tax_percent || 0)
    const taxAmount = (subtotal - discountAmount) * taxPercent / 100
    const shippingAmount = Number(payload.shipping_amount || 0)
    const total = subtotal - discountAmount + taxAmount + shippingAmount
    const quote = {
      id: `Q-${1043 + db.quotes.length}`,
      database_id: Date.now(),
      customer: payload.customer,
      items: payload.items || [],
      subtotal,
      discount_percent: discountPercent,
      discount_amount: discountAmount,
      tax_percent: taxPercent,
      tax_amount: taxAmount,
      shipping_amount: shippingAmount,
      amount: total,
      status: 'Draft',
      date: new Date().toISOString().slice(0, 10),
      notes: payload.notes || '',
      history: [],
    }
    quote.history = [addDemoQuoteRevision(quote, 'Created').history[0]]
    db.quotes = [quote, ...db.quotes]
    if (payload.configuration_id) {
      db.furnitureConfigurations = db.furnitureConfigurations.map((configuration) => Number(configuration.id) === Number(payload.configuration_id)
        ? { ...configuration, quote_id: quote.id, status: 'Quoted', updated_at: new Date().toISOString() }
        : configuration)
    }
    saveLocalDb(db)
    return { item: quote, mode: 'demo' }
  }
}

export async function getQuotePresets() {
  try { return await backendRequest('/quote-config/presets') }
  catch (error) {
    if (error.status) throw error
    await delay()
    return { items: getLocalDb().quotePresets, mode: 'demo' }
  }
}

export async function createQuotePreset(payload) {
  try { return await backendRequest('/quote-config/presets', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const item = { ...payload, id: Math.max(0, ...db.quotePresets.map((preset) => Number(preset.id) || 0)) + 1 }
    db.quotePresets = [item, ...db.quotePresets]
    saveLocalDb(db)
    return { item, mode: 'demo' }
  }
}

export async function getCustomerPricing(customerId) {
  try { return await backendRequest(`/quote-config/pricing/${customerId}`) }
  catch (error) {
    if (error.status) throw error
    await delay()
    return { item: getLocalDb().customerPricing.find((pricing) => Number(pricing.customer_id) === Number(customerId)) || { customer_id: customerId, tier: 'Standard', discount_percent: 0 }, mode: 'demo' }
  }
}

export async function saveCustomerPricing(customerId, payload) {
  try { return await backendRequest(`/quote-config/pricing/${customerId}`, { method: 'PUT', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const current = { customer_id: customerId, ...payload }
    db.customerPricing = [...db.customerPricing.filter((pricing) => Number(pricing.customer_id) !== Number(customerId)), current]
    saveLocalDb(db)
    return { item: current, mode: 'demo' }
  }
}

export async function updateQuoteStatus(id, status) {
  try {
    return await backendRequest(`/quotes/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    db.quotes = db.quotes.map((quote) => quote.database_id === id || quote.id === id
      ? addDemoQuoteRevision({ ...quote, status }, `Status changed to ${status}`)
      : quote)
    addDemoNotification(db, 4, 'Quotation updated', `${id} is now ${status}.`, 'quote', 'quote', id)
    saveLocalDb(db)
    return { item: db.quotes.find((quote) => quote.database_id === id || quote.id === id), mode: 'demo' }
  }
}

export async function getLeads() {
  try { return await backendRequest('/leads') }
  catch (error) {
    if (error.status) throw error
    const items = getLocalDb().leads.map((lead) => ({ notes: [], tasks: [], ...lead }))
    return { items, team: getLocalDb().users.filter((user) => ['admin', 'sales'].includes(user.role)).map(({ password, ...user }) => user), mode: 'demo' }
  }
}

export async function updateLeadStage(id, stage) {
  try { return await backendRequest(`/leads/${id}`, { method: 'PATCH', body: JSON.stringify({ stage }) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb()
    db.leads = db.leads.map((lead) => Number(lead.id) === Number(id) ? { ...lead, stage } : lead)
    saveLocalDb(db)
    return { item: db.leads.find((lead) => Number(lead.id) === Number(id)), mode: 'demo' }
  }
}

export async function updateLead(id, payload) {
  try { return await backendRequest(`/leads/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.leads = db.leads.map((lead) => Number(lead.id) === Number(id) ? { ...lead, ...payload } : lead); saveLocalDb(db)
    return { item: db.leads.find((lead) => Number(lead.id) === Number(id)), mode: 'demo' }
  }
}

export async function createLead(payload) {
  try {
    return await backendRequest('/leads', { method: 'POST', body: JSON.stringify(payload) })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const lead = {
      id: Math.max(0, ...db.leads.map((item) => Number(item.id) || 0)) + 1,
      email: '',
      phone: '',
      source: 'Website',
      stage: 'New',
      value: 0,
      owner_id: null,
      owner: null,
      notes: [],
      tasks: [],
      ...payload,
      value: Number(payload.value || 0),
    }
    db.leads = [lead, ...db.leads]
    addDemoNotification(db, 1, 'New lead captured', `${lead.name} was added to the pipeline.`, 'lead', 'lead', lead.id)
    saveLocalDb(db)
    return { item: lead, mode: 'demo' }
  }
}

export async function addLeadNote(id, body) {
  try { return await backendRequest(`/leads/${id}/notes`, { method: 'POST', body: JSON.stringify({ body }) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const lead = db.leads.find((item) => Number(item.id) === Number(id)); lead.notes = [{ id: Date.now(), body, author: 'Demo user', created_at: new Date().toISOString() }, ...(lead.notes || [])]; saveLocalDb(db); return { lead, mode: 'demo' }
  }
}

export async function addLeadTask(id, payload) {
  try { return await backendRequest(`/leads/${id}/tasks`, { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const lead = db.leads.find((item) => Number(item.id) === Number(id)); const task = { id: Date.now(), is_done: false, ...payload }; lead.tasks = [...(lead.tasks || []), task]; addDemoNotification(db, 1, 'Lead follow-up assigned', `${task.title} for ${lead.name}.`, 'task', 'lead', lead.id); saveLocalDb(db); return { item: task, lead, mode: 'demo' }
  }
}

export async function updateLeadTask(leadId, taskId, payload) {
  try { return await backendRequest(`/leads/${leadId}/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const lead = db.leads.find((item) => Number(item.id) === Number(leadId)); lead.tasks = (lead.tasks || []).map((task) => Number(task.id) === Number(taskId) ? { ...task, ...payload } : task); saveLocalDb(db); return { mode: 'demo' }
  }
}

export async function getOrders() {
  try { return await backendRequest('/orders') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().orders, mode: 'demo' } }
}

export async function createOrder(payload) {
  try { return await backendRequest('/orders', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const quote = db.quotes.find((item) => item.database_id === Number(payload.quote_id) || item.id === payload.quote_id)
    if (!quote) throw new Error('Choose a valid quotation.')
    const order = { id: Date.now(), order_number: `ORD-${1001 + db.orders.length}`, quote_id: quote.database_id, quote_number: quote.id, customer: quote.customer, status: 'Confirmed', production_status: 'Not started', delivery_date: payload.delivery_date || null, installation_status: 'Not scheduled', amount: Number(quote.amount || 0), notes: payload.notes || '', updates: [] }
    db.orders = [order, ...db.orders]; saveLocalDb(db); return { item: order, mode: 'demo' }
  }
}

export async function updateOrder(id, payload) {
  try { return await backendRequest(`/orders/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.orders = db.orders.map((order) => Number(order.id) === Number(id) ? { ...order, ...payload } : order); saveLocalDb(db)
    return { item: db.orders.find((order) => Number(order.id) === Number(id)), mode: 'demo' }
  }
}

export async function addOrderUpdate(id, body) {
  try { return await backendRequest(`/orders/${id}/updates`, { method: 'POST', body: JSON.stringify({ body }) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(id)); const update = { id: Date.now(), body, author: 'Demo user', created_at: new Date().toISOString() }; order.updates = [update, ...(order.updates || [])]; saveLocalDb(db); return { item: update, order, mode: 'demo' }
  }
}

export async function getInventory() {
  try { return await backendRequest('/inventory') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().inventory, mode: 'demo' } }
}

export async function createInventory(payload) {
  try { return await backendRequest('/inventory', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const product = db.products.find((item) => Number(item.id) === Number(payload.product_id)); if (!product) throw new Error('Choose a valid product.')
    const item = { id: Date.now(), product_id: product.id, product: product.name, sku: product.sku, quantity: Number(payload.quantity || 0), reserved_quantity: Number(payload.reserved_quantity || 0), reorder_level: Number(payload.reorder_level || 0), supplier: payload.supplier || '', location: payload.location || '' }
    item.available_quantity = Math.max(item.quantity - item.reserved_quantity, 0); item.is_low_stock = item.available_quantity <= item.reorder_level; db.inventory = [item, ...db.inventory]; saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function updateInventory(id, payload) {
  try { return await backendRequest(`/inventory/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.inventory = db.inventory.map((item) => { if (Number(item.id) !== Number(id)) return item; const next = { ...item, ...payload }; next.available_quantity = Math.max(Number(next.quantity || 0) - Number(next.reserved_quantity || 0), 0); next.is_low_stock = next.available_quantity <= Number(next.reorder_level || 0); return next }); saveLocalDb(db); return { item: db.inventory.find((item) => Number(item.id) === Number(id)), mode: 'demo' }
  }
}

export async function getNotifications() {
  try { return await backendRequest('/notifications') }
  catch (error) {
    if (error.status) throw error
    await delay()
    const user = JSON.parse(localStorage.getItem('furnivo-user') || 'null')
    return { items: getLocalDb().notifications.filter((item) => !item.user_id || item.user_id === user?.id), mode: 'demo' }
  }
}

export async function markNotificationRead(id) {
  try { return await backendRequest(`/notifications/${id}/read`, { method: 'PATCH' }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.notifications = db.notifications.map((item) => Number(item.id) === Number(id) ? { ...item, is_read: true } : item); saveLocalDb(db); return { mode: 'demo' }
  }
}

export async function deliverNotification(id, channel, recipient = '') {
  try { return await backendRequest(`/notifications/${id}/deliver`, { method: 'POST', body: JSON.stringify({ channel, recipient }) }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    return { item: { id: Date.now(), notification_id: id, channel, recipient, status: 'demo-queued', error: 'Configure the provider in the backend environment for live delivery.' }, mode: 'demo' }
  }
}

export async function retryNotificationDelivery(deliveryId) {
  try { return await backendRequest(`/notifications/deliveries/${deliveryId}/retry`, { method: 'POST' }) }
  catch (error) { if (error.status) throw error; await delay(); return { item: { id: deliveryId, status: 'demo-queued', error: 'Connect the notification provider to retry delivery.' }, mode: 'demo' } }
}

export async function getInvoices() {
  try { return await backendRequest('/invoices') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().invoices, mode: 'demo' } }
}

export async function createInvoice(payload) {
  try { return await backendRequest('/invoices', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); if (!order) throw new Error('Choose a valid order.')
    if (db.invoices.some((item) => Number(item.order_id) === Number(order.id))) throw new Error('An invoice already exists for this order.')
    const invoiceNumber = `INV-${2001 + db.invoices.length}`; const invoice = { id: Date.now(), invoice_number: invoiceNumber, order_id: order.id, order_number: order.order_number, customer: order.customer, issue_date: new Date().toISOString().slice(0, 10), due_date: payload.due_date || '', status: 'Sent', subtotal: Number(order.amount || 0), tax_amount: 0, total: Number(order.amount || 0), amount_paid: 0, balance: Number(order.amount || 0), payment_link: `/pay/${invoiceNumber}`, payments: [] }; db.invoices = [invoice, ...db.invoices]; saveLocalDb(db); return { item: invoice, mode: 'demo' }
  }
}

export async function recordPayment(id, payload) {
  try { return await backendRequest(`/invoices/${id}/payments`, { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const invoice = db.invoices.find((item) => Number(item.id) === Number(id)); const amount = Number(payload.amount || 0); if (!invoice || amount <= 0 || amount > Number(invoice.balance)) throw new Error('Payment amount is invalid.')
    const payment = { id: Date.now(), amount, method: payload.method || 'Bank transfer', reference: payload.reference || '', paid_at: new Date().toISOString() }; invoice.amount_paid = Number(invoice.amount_paid || 0) + amount; invoice.balance = Math.max(Number(invoice.total) - invoice.amount_paid, 0); invoice.status = invoice.balance === 0 ? 'Paid' : 'Partially Paid'; invoice.payments = [payment, ...(invoice.payments || [])]; saveLocalDb(db); return { item: invoice, mode: 'demo' }
  }
}

export async function createCheckout(id, idempotencyKey = `checkout-${id}-${Date.now()}`) {
  try { return await backendRequest(`/payments/invoices/${id}/checkout`, { method: 'POST', headers: { 'Idempotency-Key': idempotencyKey } }) }
  catch (error) { if (error.status) throw error; await delay(); const invoice = getLocalDb().invoices.find((item) => Number(item.id) === Number(id)); return { item: { provider: 'demo', external_id: `demo_${Date.now()}`, checkout_url: invoice?.payment_link || `/pay/${id}`, amount: Number(invoice?.balance || 0), status: 'demo-checkout' }, mode: 'demo' } }
}

export async function getSuppliers() {
  try { return await backendRequest('/procurement/suppliers') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().suppliers, mode: 'demo' } }
}

export async function createSupplier(payload) {
  try { return await backendRequest('/procurement/suppliers', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const item = { id: Date.now(), ...payload }; db.suppliers = [item, ...db.suppliers]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function getPurchaseOrders() {
  try { return await backendRequest('/procurement/purchase-orders') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().purchaseOrders, mode: 'demo' } }
}

export async function createPurchaseOrder(payload) {
  try { return await backendRequest('/procurement/purchase-orders', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const supplier = db.suppliers.find((item) => Number(item.id) === Number(payload.supplier_id)); const items = (payload.items || []).map((item, index) => ({ id: Date.now() + index, ...item, quantity: Number(item.quantity), unit_cost: Number(item.unit_cost), line_total: Number(item.quantity) * Number(item.unit_cost) })); const po = { id: Date.now(), po_number: `PO-${3001 + db.purchaseOrders.length}`, supplier_id: supplier?.id, supplier: supplier?.name, status: 'Draft', order_date: new Date().toISOString().slice(0, 10), expected_date: payload.expected_date || '', notes: payload.notes || '', total: items.reduce((sum, item) => sum + item.line_total, 0), items }; db.purchaseOrders = [po, ...db.purchaseOrders]; saveLocalDb(db); return { item: po, mode: 'demo' } }
}

export async function updatePurchaseOrder(id, payload) {
  try { return await backendRequest(`/procurement/purchase-orders/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.purchaseOrders = db.purchaseOrders.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload } : item); saveLocalDb(db); return { item: db.purchaseOrders.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getReportSummary() {
  try { return await backendRequest('/reports/summary') }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb(); const quotes = db.quotes; const leads = db.leads; const orders = db.orders; const invoices = db.invoices; const payments = invoices.flatMap((item) => item.payments || [])
    return { data: { quotes: { count: quotes.length, value: quotes.reduce((sum, item) => sum + Number(item.amount || 0), 0) }, leads: { count: leads.length, value: leads.reduce((sum, item) => sum + Number(item.value || 0), 0), won: leads.filter((item) => item.stage === 'Won').length }, orders: { count: orders.length, value: orders.reduce((sum, item) => sum + Number(item.amount || 0), 0) }, invoices: { count: invoices.length, value: invoices.reduce((sum, item) => sum + Number(item.total || 0), 0), paid: invoices.reduce((sum, item) => sum + Number(item.amount_paid || 0), 0), balance: invoices.reduce((sum, item) => sum + Number(item.balance || 0), 0) }, payments: { count: payments.length, value: payments.reduce((sum, item) => sum + Number(item.amount || 0), 0) }, inventory: { items: db.inventory.length, low_stock: db.inventory.filter((item) => item.is_low_stock).length, available_units: db.inventory.reduce((sum, item) => sum + Number(item.available_quantity || 0), 0) } }, mode: 'demo' }
  }
}

export async function getAuditLogs(resource = '') {
  try { return await backendRequest(`/audit-logs${resource ? `?resource=${encodeURIComponent(resource)}` : ''}`) }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().auditLogs, mode: 'demo' } }
}

export async function getSchedules() {
  try { return await backendRequest('/schedules') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().schedules, mode: 'demo' } }
}

export async function createSchedule(payload) {
  try { return await backendRequest('/schedules', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), order_id: order?.id, order_number: order?.order_number, customer: order?.customer, status: 'Scheduled', ...payload }; db.schedules = [item, ...db.schedules]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function updateSchedule(id, payload) {
  try { return await backendRequest(`/schedules/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.schedules = db.schedules.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload } : item); saveLocalDb(db); return { item: db.schedules.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getWarehouses() {
  try { return await backendRequest('/warehouses') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().warehouses, mode: 'demo' } }
}
export async function getWarehouseStock() {
  try { return await backendRequest('/warehouses/stock') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().warehouseStock, mode: 'demo' } }
}
export async function getStockMovements() {
  try { return await backendRequest('/warehouses/movements') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().stockMovements, mode: 'demo' } }
}
export async function createWarehouse(payload) {
  try { return await backendRequest('/warehouses', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const item = { id: Date.now(), ...payload }; db.warehouses = [...db.warehouses, item]; saveLocalDb(db); return { item, mode: 'demo' } }
}
export async function transferStock(payload) {
  try { return await backendRequest('/warehouses/transfer', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const source = db.warehouseStock.find((item) => Number(item.warehouse_id) === Number(payload.from_warehouse_id) && Number(item.product_id) === Number(payload.product_id)); const target = db.warehouseStock.find((item) => Number(item.warehouse_id) === Number(payload.to_warehouse_id) && Number(item.product_id) === Number(payload.product_id)); const quantity = Number(payload.quantity); if (!source || Number(source.available_quantity) < quantity) throw new Error('Not enough available stock.'); source.quantity -= quantity; source.available_quantity -= quantity; if (target) { target.quantity += quantity; target.available_quantity += quantity } const movement = { id: Date.now(), from_warehouse: source.warehouse, to_warehouse: target?.warehouse || 'New warehouse', product: source.product, quantity, movement_type: 'Transfer', reference: payload.reference || '', created_at: new Date().toISOString() }; db.stockMovements = [movement, ...db.stockMovements]; saveLocalDb(db); return { item: movement, mode: 'demo' } }
}

export async function getReturns() {
  try { return await backendRequest('/returns') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().returns, mode: 'demo' } }
}
export async function createReturn(payload) {
  try { return await backendRequest('/returns', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), order_id: order?.id, order_number: order?.order_number, customer: order?.customer, status: 'Requested', credit_note: null, created_at: new Date().toISOString(), ...payload, amount: Number(payload.amount) }; db.returns = [item, ...db.returns]; saveLocalDb(db); return { item, mode: 'demo' } }
}
export async function updateReturn(id, payload) {
  try { return await backendRequest(`/returns/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.returns = db.returns.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload, credit_note: payload.status === 'Approved' ? { credit_note_number: `CN-${4000 + Number(id)}`, amount: item.amount, status: 'Issued' } : item.credit_note } : item); saveLocalDb(db); return { item: db.returns.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getProductionJobs() {
  try { return await backendRequest('/production') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().productionJobs, mode: 'demo' } }
}

export async function createProductionJob(payload) {
  try { return await backendRequest('/production', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), job_number: `JOB-${5000 + db.productionJobs.length + 1}`, customer: order?.customer, order_number: order?.order_number, status: 'Planned', ...payload, bom_items: payload.bom_items || [] }; db.productionJobs = [item, ...db.productionJobs]; saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function updateProductionJob(id, payload) {
  try { return await backendRequest(`/production/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.productionJobs = db.productionJobs.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload } : item); saveLocalDb(db); return { item: db.productionJobs.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getPaymentReconciliations() {
  try { return await backendRequest('/payment-reconciliation') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().paymentReconciliations, mode: 'demo' } }
}

export async function reconcilePayment(payload) {
  try { return await backendRequest('/payment-reconciliation', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const invoice = db.invoices.find((item) => Number(item.id) === Number(payload.invoice_id)); const item = { id: Date.now(), invoice_id: invoice?.id, invoice_number: invoice?.invoice_number, customer: invoice?.customer, provider: payload.provider || 'Manual', external_id: payload.external_id, amount: Number(payload.amount), refunded_amount: 0, refundable_amount: Number(payload.amount), status: payload.status || 'Paid', refund_status: 'Not refunded', provider_refund_id: '', dispute_reason: payload.dispute_reason || '', created_at: new Date().toISOString() }; if (item.status === 'Paid' && invoice) { invoice.amount_paid += item.amount; invoice.balance = Math.max(Number(invoice.total) - invoice.amount_paid, 0) } db.paymentReconciliations = [item, ...db.paymentReconciliations]; saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function refundReconciledPayment(id, payload = {}) {
  try { return await backendRequest(`/payments/reconciliation/${id}/refund`, { method: 'POST', headers: { 'Idempotency-Key': payload.idempotency_key || `refund-${id}-${payload.amount || 'full'}` }, body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const item = db.paymentReconciliations.find((entry) => Number(entry.id) === Number(id)); const amount = Number(payload.amount || item?.refundable_amount || 0); if (!item || amount <= 0 || amount > Number(item.refundable_amount)) throw new Error('Refund amount exceeds the refundable balance.'); item.refunded_amount += amount; item.refundable_amount -= amount; item.refund_status = item.refundable_amount === 0 ? 'Refunded' : 'Partially refunded'; const invoice = db.invoices.find((entry) => Number(entry.id) === Number(item.invoice_id)); if (invoice) { invoice.amount_paid = Math.max(Number(invoice.amount_paid) - amount, 0); invoice.balance = Math.max(Number(invoice.total) - invoice.amount_paid, 0) } saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function downloadPaymentReceipt(id, invoiceNumber = 'payment-receipt') {
  if (API_URL) { const token = localStorage.getItem('furnivo-token'); const response = await fetch(`${API_URL}/payments/reconciliation/${id}/receipt`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }); if (!response.ok) throw new Error('Could not download receipt.'); const url = URL.createObjectURL(await response.blob()); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${invoiceNumber}-receipt.pdf`; anchor.click(); URL.revokeObjectURL(url); return { mode: 'api' } }
  const item = getLocalDb().paymentReconciliations.find((entry) => Number(entry.id) === Number(id)); const url = URL.createObjectURL(new Blob([`FURNIVO PAYMENT RECEIPT\n${item?.invoice_number}\nAmount: INR ${item?.amount}\nStatus: ${item?.status}`], { type: 'text/plain' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${invoiceNumber}-receipt.txt`; anchor.click(); URL.revokeObjectURL(url); return { mode: 'demo' }
}

export async function getContracts() {
  try { return await backendRequest('/contracts') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().contracts, mode: 'demo' } }
}

export async function createContract(payload) {
  try { return await backendRequest('/contracts', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const quote = db.quotes.find((item) => Number(item.database_id || item.id) === Number(payload.quote_id)); const item = { id: Date.now(), contract_number: `CTR-${7000 + db.contracts.length + 1}`, quote_id: payload.quote_id, quote_number: quote?.id, customer: quote?.customer, status: 'Sent', locked: false, signatures: [], ...payload }; db.contracts = [item, ...db.contracts]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function signContract(id, signature_text) {
  try { return await backendRequest(`/contracts/${id}/sign`, { method: 'POST', body: JSON.stringify({ signature_text }) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb()
    const item = db.contracts.find((contract) => Number(contract.id) === Number(id))
    if (!item || item.locked) throw new Error('This contract is locked.')
    item.status = 'Signed'
    item.locked = true
    item.signed_at = new Date().toISOString()
    item.signatures = [{ id: Date.now(), signer_name: JSON.parse(localStorage.getItem('furnivo-user') || '{}').name || 'Client', signer_role: 'client', signature_text, signed_at: item.signed_at }]
    const quote = db.quotes.find((quoteItem) => Number(quoteItem.database_id || quoteItem.id) === Number(item.quote_id))
    let order = db.orders.find((orderItem) => Number(orderItem.quote_id) === Number(item.quote_id))
    let invoice = order && db.invoices.find((invoiceItem) => Number(invoiceItem.order_id) === Number(order.id))
    let created = false
    if (!order && quote) {
      const depositPercent = 30
      const total = Number(quote.amount || 0)
      const depositTotal = Math.round(total * depositPercent) / 100
      order = { id: Date.now(), order_number: `ORD-${1001 + db.orders.length}`, quote_id: quote.database_id || quote.id, quote_number: quote.id, customer: quote.customer, status: 'Awaiting deposit', production_status: 'Not started', delivery_date: null, installation_status: 'Not scheduled', amount: total, notes: `Automatically created after signed contract. Deposit required: ${depositPercent}%.`, updates: [] }
      const invoiceNumber = `INV-${2001 + db.invoices.length}`
      invoice = { id: Date.now() + 1, invoice_number: invoiceNumber, order_id: order.id, order_number: order.order_number, customer: quote.customer, issue_date: new Date().toISOString().slice(0, 10), due_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10), status: 'Sent', invoice_type: 'Deposit', deposit_percent: depositPercent, subtotal: Number(quote.subtotal || total) * depositPercent / 100, tax_amount: Number(quote.tax_amount || 0) * depositPercent / 100, total: depositTotal, amount_paid: 0, balance: depositTotal, payment_link: `/pay/${invoiceNumber}`, notes: `${depositPercent}% advance payment for ${quote.id}. The final balance will be invoiced separately.`, payments: [] }
      db.orders = [order, ...db.orders]
      db.invoices = [invoice, ...db.invoices]
      created = true
    }
    saveLocalDb(db)
    return { item, automation: { order, invoice, created }, mode: 'demo' }
  }
}

export async function updateContract(id, payload) {
  try { return await backendRequest(`/contracts/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.contracts = db.contracts.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload } : item); saveLocalDb(db); return { item: db.contracts.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function downloadContractPdf(contract) {
  if (API_URL && contract.id) {
    try { const token = localStorage.getItem('furnivo-token'); const response = await fetch(`${API_URL}/contracts/${contract.id}/pdf`, { headers: token ? { Authorization: `Bearer ${token}` } : {} }); if (!response.ok) throw new Error('Could not download contract.'); const blob = await response.blob(); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${contract.contract_number}.pdf`; anchor.click(); URL.revokeObjectURL(url); return { mode: 'api' } } catch (error) { if (error.status) throw error }
  }
  const body = `${contract.title}\n\n${contract.terms}\n\nStatus: ${contract.status}`; const url = URL.createObjectURL(new Blob([body], { type: 'text/plain' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${contract.contract_number}.txt`; anchor.click(); URL.revokeObjectURL(url); return { mode: 'demo' }
}

export async function getProjectPortal() {
  try { return await backendRequest('/portal') }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    const projects = db.orders.map((order) => ({ order, production: db.productionJobs.find((job) => Number(job.order_id) === Number(order.id)), schedules: db.schedules.filter((schedule) => Number(schedule.order_id) === Number(order.id)), invoice: db.invoices.find((invoice) => Number(invoice.order_id) === Number(order.id)), contract: db.contracts.find((contract) => String(contract.quote_id) === String(order.quote_id) || contract.quote_number === order.quote_number) }))
    return { projects, documents: db.contracts.map((contract) => ({ type: 'Contract', number: contract.contract_number, status: contract.status, id: contract.id })).concat(db.invoices.map((invoice) => ({ type: 'Invoice', number: invoice.invoice_number, status: invoice.status, amount: invoice.total }))), support_tickets: db.supportTickets, mode: 'demo' }
  }
}

export async function createSupportTicket(payload) {
  try { return await backendRequest('/portal/tickets', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), order_id: order?.id, order_number: order?.order_number, status: 'Open', response: '', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...payload }; db.supportTickets = [item, ...db.supportTickets]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function getOpsHealth() {
  try { return await backendRequest('/ops/health') }
  catch (error) { if (error.status) throw error; await delay(); return { ...demoOpsHealth, mode: 'demo' } }
}

export async function getBackups() {
  try { return await backendRequest('/ops/backups') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().backups, mode: 'demo' } }
}

export async function createBackup() {
  try { return await backendRequest('/ops/backups', { method: 'POST' }) }
  catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb(); const item = { filename: `furnivo-demo-${Date.now()}.json`, size_bytes: JSON.stringify(db).length, created_at: new Date().toISOString() }; db.backups = [item, ...db.backups]; saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function getEInvoices() {
  try { return await backendRequest('/gst') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().eInvoices, mode: 'demo' } }
}

export async function generateEInvoice(invoiceId, payload) {
  try { return await backendRequest(`/gst/invoices/${invoiceId}/generate`, { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const invoice = db.invoices.find((item) => Number(item.id) === Number(invoiceId)); const tax = Number(invoice?.tax_amount || 0); const item = { id: Date.now(), invoice_id: invoiceId, invoice_number: invoice?.invoice_number, customer: invoice?.customer, gstin: payload.gstin || '', place_of_supply: payload.place_of_supply || '', tax_mode: payload.tax_mode || 'CGST/SGST', hsn_summary: payload.hsn_summary || [{ hsn: '9403', description: 'Furniture and interiors', taxable_value: invoice?.subtotal || 0 }], cgst_amount: payload.tax_mode === 'IGST' ? 0 : tax / 2, sgst_amount: payload.tax_mode === 'IGST' ? 0 : tax / 2, igst_amount: payload.tax_mode === 'IGST' ? tax : 0, irn: `DEMO-${invoice?.invoice_number}-${Date.now()}`, acknowledgement_number: `ACK-${Date.now()}`, status: 'Generated', eway_bill_number: '', created_at: new Date().toISOString() }; db.eInvoices = [item, ...db.eInvoices]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function generateEwayBill(id) {
  try { return await backendRequest(`/gst/${id}/eway-bill`, { method: 'POST', body: JSON.stringify({}) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.eInvoices = db.eInvoices.map((item) => Number(item.id) === Number(id) ? { ...item, eway_bill_number: `EWB-${Date.now()}`, status: 'E-way bill generated' } : item); saveLocalDb(db); return { item: db.eInvoices.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getBackgroundJobs() {
  try { return await backendRequest('/data-admin/jobs') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().backgroundJobs, mode: 'demo' } }
}

export async function createBackgroundJob(job_type) {
  try { return await backendRequest('/data-admin/jobs', { method: 'POST', body: JSON.stringify({ job_type }) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const item = { id: Date.now(), job_type, status: 'Complete', payload: {}, result: { demo: true }, error: '', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }; db.backgroundJobs = [item, ...db.backgroundJobs]; saveLocalDb(db); return { item, mode: 'demo' } }
}

async function uploadCsv(path, file) {
  if (API_URL) { const token = localStorage.getItem('furnivo-token'); const body = new FormData(); body.append('file', file); const response = await fetch(`${API_URL}${path}`, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, body }); const data = await response.json().catch(() => ({})); if (!response.ok) { const error = new Error(data.message || 'CSV import failed.'); error.status = response.status; throw error } return data }
  await delay(); return { created: 0, updated: 0, errors: 0, mode: 'demo', message: 'Demo mode does not persist CSV files.' }
}

export async function importProductsCsv(file) { return uploadCsv('/data-admin/products/import', file) }
export async function importCustomersCsv(file) { return uploadCsv('/data-admin/customers/import', file) }


export async function createProduct(payload) {
  try {
    return await backendRequest('/products', { method: 'POST', body: JSON.stringify(payload) })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    if (db.products.some((item) => item.sku.toLowerCase() === payload.sku.toLowerCase())) {
      throw new Error('SKU must be unique.')
    }
    const product = {
      id: Math.max(0, ...db.products.map((item) => Number(item.id) || 0)) + 1,
      description: '',
      is_active: true,
      ...payload,
      price: Number(payload.price || 0),
    }
    db.products.push(product)
    saveLocalDb(db)
    return { item: product, mode: 'demo' }
  }
}

export async function updateProduct(id, payload) {
  try {
    return await backendRequest(`/products/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    db.products = db.products.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload, price: Number(payload.price ?? item.price) } : item)
    saveLocalDb(db)
    return { item: db.products.find((item) => Number(item.id) === Number(id)), mode: 'demo' }
  }
}

export async function deleteProduct(id) {
  try {
    return await backendRequest(`/products/${id}`, { method: 'DELETE' })
  } catch (error) {
    if (error.status) throw error
    await delay()
    const db = getLocalDb()
    db.products = db.products.filter((item) => Number(item.id) !== Number(id))
    saveLocalDb(db)
    return { ok: true, mode: 'demo' }
  }
}

export async function createProductVariant(productId, payload) {
  try {
    return await backendRequest(`/products/${productId}/variants`, { method: 'POST', body: JSON.stringify(payload) })
  } catch (error) {
    if (error.status) throw error
    const db = getLocalDb()
    const product = db.products.find((item) => Number(item.id) === Number(productId))
    const variants = product.variants || []
    const variant = { id: Date.now(), product_id: productId, ...payload, price_delta: Number(payload.price_delta || 0) }
    product.variants = [...variants, variant]
    saveLocalDb(db)
    return { item: variant, mode: 'demo' }
  }
}

export async function deleteProductVariant(productId, variantId) {
  try {
    return await backendRequest(`/products/${productId}/variants/${variantId}`, { method: 'DELETE' })
  } catch (error) {
    if (error.status) throw error
    const db = getLocalDb()
    const product = db.products.find((item) => Number(item.id) === Number(productId))
    product.variants = (product.variants || []).filter((item) => Number(item.id) !== Number(variantId))
    saveLocalDb(db)
    return { ok: true, mode: 'demo' }
  }
}

export async function uploadProductImage(file) {
  if (API_URL) {
    try {
      const token = localStorage.getItem('furnivo-token')
      const body = new FormData()
      body.append('file', file)
      const response = await fetch(`${API_URL}/uploads/product-image`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body,
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        const error = new Error(data.message || 'Image upload failed')
        error.status = response.status
        throw error
      }
      if (data.item?.url?.startsWith('/')) {
        const origin = API_URL.replace(/\/api$/, '')
        data.item.url = `${origin}${data.item.url}`
      }
      return data
    } catch (error) {
      if (error.status) throw error
      setDataMode('demo')
    }
  }

  if (file.size > 1_500_000) throw new Error('Demo image must be under 1.5 MB.')
  const url = await new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
  return { item: { url, provider: 'browser-demo' }, mode: 'demo' }
}

export async function uploadFieldProof(file, visitId) {
  if (API_URL) {
    try {
      const token = localStorage.getItem('furnivo-token'); const body = new FormData(); body.append('file', file); body.append('visit_id', String(visitId || ''))
      const response = await fetch(`${API_URL}/uploads/field-proof`, { method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : {}, body })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) { const error = new Error(data.message || 'Proof upload failed'); error.status = response.status; throw error }
      if (data.item?.url?.startsWith('/')) data.item.url = `${API_URL.replace(/\/api$/, '')}${data.item.url}`
      return data
    } catch (error) { if (error.status) throw error; setDataMode('demo') }
  }
  if (file.size > 1_500_000) throw new Error('Demo image must be under 1.5 MB.')
  const url = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(file) })
  return { item: { url, provider: 'browser-demo' }, mode: 'demo' }
}

export async function downloadQuotePdf(quote) {
  if (API_URL && quote.database_id) {
    try {
      const token = localStorage.getItem('furnivo-token')
      const response = await fetch(`${API_URL}/quotes/${quote.database_id}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!response.ok) {
        const error = new Error('Could not generate quotation PDF.')
        error.status = response.status
        throw error
      }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${quote.id}.pdf`
      anchor.click()
      URL.revokeObjectURL(url)
      return { mode: 'api' }
    } catch (error) {
      if (error.status) throw error
    }
  }

  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF()
  doc.setFontSize(20)
  doc.text('FURNIVO', 16, 20)
  doc.setFontSize(10)
  doc.text(`Quotation: ${quote.id}`, 16, 30)
  doc.text(`Customer: ${quote.customer}`, 16, 36)
  doc.text(`Date: ${quote.date}`, 16, 42)
  let y = 54
  ;(quote.items || []).forEach((item, index) => {
    const amount = Number(item.quantity || 0) * Number(item.unit_price || 0)
    doc.text(`${index + 1}. ${item.description || item.sku || 'Item'} | ${item.quantity} x INR ${Number(item.unit_price || 0).toLocaleString('en-IN')} = INR ${amount.toLocaleString('en-IN')}`, 16, y)
    y += 7
  })
  doc.setFontSize(12)
  doc.text(`Total: INR ${Number(quote.amount || 0).toLocaleString('en-IN')}`, 16, y + 8)
  doc.save(`${quote.id}.pdf`)
  return { mode: 'demo' }
}


export async function getCustomers(options = {}) {
  const query = new URLSearchParams(Object.entries(options).filter(([, value]) => value !== undefined && value !== ''))
  try { return await backendRequest(`/customers${query.toString() ? `?${query}` : ''}`) }
  catch (error) { if (error.status) throw error; const all = getLocalDb().customers.filter((item) => options.include_archived === 'true' || item.is_active !== false).filter((item) => !options.q || `${item.company} ${item.contact_name} ${item.email}`.toLowerCase().includes(String(options.q).toLowerCase())); return { items: all, pagination: { page: 1, page_size: all.length, total: all.length, pages: 1 }, mode: 'demo' } }
}

export async function createCustomer(payload) {
  try { return await backendRequest('/customers', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb()
    const item = { id: Math.max(0, ...db.customers.map((c) => Number(c.id) || 0)) + 1, ...payload }
    db.customers.push(item); saveLocalDb(db); return { item, mode: 'demo' }
  }
}

export async function updateCustomer(id, payload) {
  try { return await backendRequest(`/customers/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.customers = db.customers.map((c) => Number(c.id) === Number(id) ? { ...c, ...payload } : c); saveLocalDb(db)
    return { item: db.customers.find((c) => Number(c.id) === Number(id)), mode: 'demo' }
  }
}

export async function getAccessUsers() {
  try { return await backendRequest('/access/users') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().accessUsers, mode: 'demo' } }
}

export async function saveUserPermissions(userId, permissions) {
  try { return await backendRequest(`/access/users/${userId}/permissions`, { method: 'PUT', body: JSON.stringify({ permissions }) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); db.accessUsers = db.accessUsers.map((entry) => Number(entry.user.id) === Number(userId) ? { ...entry, permissions } : entry); saveLocalDb(db)
    return { item: db.accessUsers.find((entry) => Number(entry.user.id) === Number(userId)), mode: 'demo' }
  }
}

export async function getDepartments() {
  try { return await backendRequest('/access/departments') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().departments, mode: 'demo' } }
}

export async function createDepartment(payload) {
  try { return await backendRequest('/access/departments', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const item = { id: Date.now(), ...payload }; db.departments = [...db.departments, item]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function getApprovalRequests() {
  try { return await backendRequest('/access/approvals') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().approvals, mode: 'demo' } }
}

export async function createApprovalRequest(payload) {
  try { return await backendRequest('/access/approvals', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const user = JSON.parse(localStorage.getItem('furnivo-user') || '{}'); const item = { id: Date.now(), status: 'Requested', requested_by: user, approved_by: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...payload }; db.approvals = [item, ...db.approvals]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function updateApprovalRequest(id, status) {
  try { return await backendRequest(`/access/approvals/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const user = JSON.parse(localStorage.getItem('furnivo-user') || '{}'); db.approvals = db.approvals.map((item) => Number(item.id) === Number(id) ? { ...item, status, approved_by: user, updated_at: new Date().toISOString() } : item); saveLocalDb(db); return { item: db.approvals.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getProjectOwnership() {
  try { return await backendRequest('/access/ownership') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().projectOwnership, mode: 'demo' } }
}

export async function assignProjectOwner(payload) {
  try { return await backendRequest('/access/ownership', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const owner = db.users.find((item) => Number(item.id) === Number(payload.user_id)); const item = { id: Date.now(), ...payload, order_number: order?.order_number, customer: order?.customer, owner, assigned_by: JSON.parse(localStorage.getItem('furnivo-user') || '{}').name }; db.projectOwnership = [item, ...db.projectOwnership.filter((entry) => !(Number(entry.order_id) === Number(payload.order_id) && Number(entry.user_id) === Number(payload.user_id)))]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function getWarranties() {
  try { return await backendRequest('/service/warranties') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().warranties, mode: 'demo' } }
}

export async function createWarranty(payload) {
  try { return await backendRequest('/service/warranties', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), warranty_number: `WAR-${7000 + db.warranties.length + 1}`, customer: order?.customer, order_number: order?.order_number, status: 'Active', ...payload }; db.warranties = [item, ...db.warranties]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function getServiceTickets() {
  try { return await backendRequest('/service/tickets') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().serviceTickets, mode: 'demo' } }
}

export async function createServiceTicket(payload) {
  try { return await backendRequest('/service/tickets', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), ticket_number: `SVC-${8000 + db.serviceTickets.length + 1}`, order_number: order?.order_number, customer: order?.customer, status: 'Open', resolution: '', created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...payload }; db.serviceTickets = [item, ...db.serviceTickets]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function updateServiceTicket(id, payload) {
  try { return await backendRequest(`/service/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.serviceTickets = db.serviceTickets.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload, updated_at: new Date().toISOString() } : item); saveLocalDb(db); return { item: db.serviceTickets.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function getAnalytics() {
  try { return await backendRequest('/analytics') }
  catch (error) { if (error.status) throw error; await delay(); return { ...getLocalDb().analytics || demoAnalytics, mode: 'demo' } }
}

export async function getIntegrations() {
  try { return await backendRequest('/integrations') }
  catch (error) { if (error.status) throw error; await delay(); const db = getLocalDb(); return { connections: db.integrations, runs: db.syncRuns, mode: 'demo' } }
}

export async function createIntegration(payload) {
  try { return await backendRequest('/integrations', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const item = { id: Date.now(), status: 'Connected', is_enabled: true, last_sync_at: null, ...payload }; db.integrations = [item, ...db.integrations]; saveLocalDb(db); return { item, mode: 'demo' } }
}

export async function updateIntegration(id, payload) {
  try { return await backendRequest(`/integrations/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.integrations = db.integrations.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload } : item); saveLocalDb(db); return { item: db.integrations.find((item) => Number(item.id) === Number(id)), mode: 'demo' } }
}

export async function syncIntegration(id, entity = 'invoices') {
  try { return await backendRequest(`/integrations/${id}/sync`, { method: 'POST', body: JSON.stringify({ entity }) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); const connection = db.integrations.find((item) => Number(item.id) === Number(id)); const run = { id: Date.now(), connection_id: id, provider: connection?.provider, entity, status: 'Complete', records_synced: entity === 'invoices' ? db.invoices.length : 0, error: '', started_at: new Date().toISOString(), completed_at: new Date().toISOString() }; connection.last_sync_at = run.completed_at; connection.status = 'Synced'; db.syncRuns = [run, ...db.syncRuns]; saveLocalDb(db); return { item: run, connection, mode: 'demo' } }
}

function getFieldQueue() {
  try { return JSON.parse(localStorage.getItem('furnivo-field-queue') || '[]') } catch { return [] }
}

function saveFieldQueue(queue) { localStorage.setItem('furnivo-field-queue', JSON.stringify(queue)) }

export async function getFieldVisits() {
  try { return await backendRequest('/field') }
  catch (error) { if (error.status) throw error; await delay(); return { items: getLocalDb().fieldVisits, mode: 'demo' } }
}

export async function createFieldVisit(payload) {
  try { return await backendRequest('/field', { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) {
    if (error.status) throw error
    const db = getLocalDb(); const order = db.orders.find((item) => Number(item.id) === Number(payload.order_id)); const item = { id: Date.now(), order_number: order?.order_number, customer: order?.customer, status: 'Scheduled', qr_token: `FURNIVO-${Date.now().toString(36).toUpperCase()}`, offline_synced: false, ...payload }; db.fieldVisits = [item, ...db.fieldVisits]; saveLocalDb(db); const queue = getFieldQueue(); queue.push({ operation: 'create', payload: item }); saveFieldQueue(queue); return { item, mode: 'offline' }
  }
}

export async function updateFieldVisit(id, payload) {
  try { return await backendRequest(`/field/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.fieldVisits = db.fieldVisits.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload, offline_synced: false } : item); saveLocalDb(db); const queue = getFieldQueue(); queue.push({ operation: 'update', id, payload }); saveFieldQueue(queue); return { item: db.fieldVisits.find((item) => Number(item.id) === Number(id)), mode: 'offline' } }
}

export async function saveFieldProof(id, payload) {
  try { return await backendRequest(`/field/${id}/proof`, { method: 'POST', body: JSON.stringify(payload) }) }
  catch (error) { if (error.status) throw error; const db = getLocalDb(); db.fieldVisits = db.fieldVisits.map((item) => Number(item.id) === Number(id) ? { ...item, ...payload, status: 'Completed', offline_synced: false } : item); saveLocalDb(db); const queue = getFieldQueue(); queue.push({ operation: 'proof', id, payload }); saveFieldQueue(queue); return { item: db.fieldVisits.find((item) => Number(item.id) === Number(id)), mode: 'offline' } }
}

export async function syncFieldQueue() {
  const queue = getFieldQueue(); if (!queue.length) return { synced: 0, remaining: 0, mode: 'demo' }
  let synced = 0
  for (const entry of queue) {
    try { if (entry.operation === 'create') await backendRequest('/field', { method: 'POST', body: JSON.stringify(entry.payload) }); else if (entry.operation === 'proof') await backendRequest(`/field/${entry.id}/proof`, { method: 'POST', body: JSON.stringify(entry.payload) }); else await backendRequest(`/field/${entry.id}`, { method: 'PATCH', body: JSON.stringify(entry.payload) }); synced += 1 } catch (error) { if (error.status) throw error; break }
  }
  const remaining = queue.slice(synced); saveFieldQueue(remaining); return { synced, remaining: remaining.length, mode: 'api' }
}
