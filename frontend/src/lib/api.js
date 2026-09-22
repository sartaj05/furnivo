import { demoCustomers, demoInventory, demoLeads, demoOrders, demoProducts, demoQuotes, demoUsers } from '../data/demoData'

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

export async function getProducts() {
  try {
    return await backendRequest('/products')
  } catch (error) {
    if (error.status) throw error
    await delay()
    return { items: getLocalDb().products, mode: 'demo' }
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
    db.quotes = db.quotes.map((quote) => quote.database_id === id || quote.id === id
      ? addDemoQuoteRevision({ ...quote, status: action, client_access: { ...(quote.client_access || {}), last_action: action, response_comment: comment } }, `Client ${action}`, comment)
      : quote)
    saveLocalDb(db)
    return { item: db.quotes.find((quote) => quote.database_id === id || quote.id === id), mode: 'demo' }
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
    saveLocalDb(db)
    return { item: quote, mode: 'demo' }
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
    const db = getLocalDb(); const lead = db.leads.find((item) => Number(item.id) === Number(id)); const task = { id: Date.now(), is_done: false, ...payload }; lead.tasks = [...(lead.tasks || []), task]; saveLocalDb(db); return { item: task, lead, mode: 'demo' }
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


export async function getCustomers() {
  try { return await backendRequest('/customers') }
  catch (error) { if (error.status) throw error; return { items: getLocalDb().customers, mode: 'demo' } }
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
