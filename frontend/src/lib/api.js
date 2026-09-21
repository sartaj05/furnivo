import { demoLeads, demoProducts, demoQuotes, demoUsers } from '../data/demoData'

const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, '')
const STORAGE_KEY = 'furnivo-demo-db'

const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms))

function getLocalDb() {
  const existing = localStorage.getItem(STORAGE_KEY)
  if (existing) {
    const parsed = JSON.parse(existing)
    const normalized = {
      products: parsed.products || demoProducts,
      quotes: parsed.quotes || demoQuotes,
      leads: parsed.leads || demoLeads,
      users: parsed.users || demoUsers,
    }
    if (!parsed.users) localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized))
    return normalized
  }

  const initial = {
    products: demoProducts,
    quotes: demoQuotes,
    leads: demoLeads,
    users: demoUsers,
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
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(data.message || `API request failed: ${response.status}`)
    error.status = response.status
    throw error
  }
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
  } catch {
    await delay()
    return { items: getLocalDb().products, mode: 'demo' }
  }
}

export async function getQuotes() {
  try {
    return await backendRequest('/quotes')
  } catch {
    await delay()
    return { items: getLocalDb().quotes, mode: 'demo' }
  }
}

export async function createQuote(payload) {
  try {
    return await backendRequest('/quotes', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  } catch {
    await delay()
    const db = getLocalDb()
    const quote = {
      id: `Q-${1043 + db.quotes.length}`,
      customer: payload.customer,
      amount: Number(payload.amount),
      status: 'Draft',
      date: new Date().toISOString().slice(0, 10),
    }
    db.quotes = [quote, ...db.quotes]
    saveLocalDb(db)
    return { item: quote, mode: 'demo' }
  }
}

export async function getLeads() {
  try {
    return await backendRequest('/leads')
  } catch {
    await delay()
    return { items: getLocalDb().leads, mode: 'demo' }
  }
}

export async function updateLeadStage(id, stage) {
  try {
    return await backendRequest(`/leads/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ stage }),
    })
  } catch {
    await delay()
    const db = getLocalDb()
    db.leads = db.leads.map((lead) =>
      Number(lead.id) === Number(id) ? { ...lead, stage } : lead,
    )
    saveLocalDb(db)
    return { item: db.leads.find((lead) => Number(lead.id) === Number(id)), mode: 'demo' }
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
