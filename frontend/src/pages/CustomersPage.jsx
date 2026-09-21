import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { createCustomer, getCustomers, updateCustomer } from '../lib/api'

const blank = { company: '', contact_name: '', email: '', phone: '', billing_address: '', project_address: '', gstin: '', notes: '' }

export default function CustomersPage() {
  const [customers, setCustomers] = useState([])
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(blank)
  const [error, setError] = useState('')

  async function load() { setCustomers((await getCustomers()).items) }
  useEffect(() => { load() }, [])

  const filtered = useMemo(() => customers.filter((item) => `${item.company} ${item.contact_name} ${item.email} ${item.phone}`.toLowerCase().includes(query.toLowerCase())), [customers, query])

  function open(customer = null) { setEditing(customer?.id || 'new'); setForm(customer ? { ...blank, ...customer } : blank); setError('') }
  async function submit(event) {
    event.preventDefault(); setError('')
    try { if (editing === 'new') await createCustomer(form); else await updateCustomer(editing, form); setEditing(null); setForm(blank); await load() }
    catch (err) { setError(err.message) }
  }

  return <AppShell title="Customers" eyebrow="Accounts & project addresses" actions={<button className="button button-small" onClick={() => open()}>New customer</button>}>
    {editing && <form className="panel customer-editor" onSubmit={submit}><div className="panel-heading"><div><p className="eyebrow">Customer record</p><h3>{editing === 'new' ? 'Add customer' : 'Edit customer'}</h3></div><button type="button" className="text-button dark-text-button" onClick={() => setEditing(null)}>Close</button></div><div className="form-grid form-grid-3">
      <label>Company<input required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></label>
      <label>Contact name<input required value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} /></label>
      <label>Phone<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
      <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label>GSTIN<input value={form.gstin} onChange={(e) => setForm({ ...form, gstin: e.target.value })} /></label>
      <label>Billing address<input value={form.billing_address} onChange={(e) => setForm({ ...form, billing_address: e.target.value })} /></label>
      <label className="form-span-3">Project / delivery address<textarea rows="2" value={form.project_address} onChange={(e) => setForm({ ...form, project_address: e.target.value })} /></label>
      <label className="form-span-3">Notes<textarea rows="2" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
    </div>{error && <div className="form-error">{error}</div>}<button className="button">Save customer</button></form>}
    <div className="toolbar"><input className="search-input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search customer, contact, email or phone…" /></div>
    <section className="customer-grid">{filtered.map((customer) => <article className="customer-card" key={customer.id}><div className="lead-top"><div><h3>{customer.company}</h3><p>{customer.contact_name}</p></div><button className="button-link" onClick={() => open(customer)}>Edit</button></div><div className="customer-meta"><span>{customer.email || 'No email'}</span><span>{customer.phone || 'No phone'}</span><span>{customer.project_address || 'No project address'}</span>{customer.gstin && <span>GSTIN {customer.gstin}</span>}</div></article>)}</section>
  </AppShell>
}
