import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { addOrderUpdate, createOrder, getOrders, getQuotes, updateOrder } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const emptyForm = { quote_id: '', delivery_date: '', notes: '' }

export default function OrdersPage() {
  const { user } = useAuth()
  const canManage = ['admin', 'sales'].includes(user.role)
  const [orders, setOrders] = useState([])
  const [quotes, setQuotes] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [selected, setSelected] = useState(null)
  const [updateText, setUpdateText] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const result = await getOrders(); setOrders(result.items || [])
    if (canManage) setQuotes((await getQuotes()).items || [])
  }
  useEffect(() => { load() }, [])

  async function submit(event) {
    event.preventDefault(); setError('')
    try { await createOrder(form); setForm(emptyForm); setShowForm(false); await load() } catch (err) { setError(err.message) }
  }

  async function change(id, field, value) { await updateOrder(id, { [field]: value }); await load() }
  async function addUpdate(event) { event.preventDefault(); if (!updateText.trim()) return; await addOrderUpdate(selected.id, updateText); setUpdateText(''); await load(); setSelected((orders.find((order) => order.id === selected.id) || selected)) }

  return <AppShell title="Orders & projects" eyebrow="Delivery workspace" actions={canManage && <button className="button button-small" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close' : 'New order'}</button>}>
    {showForm && <form className="panel customer-editor" onSubmit={submit}><div className="panel-heading"><div><p className="eyebrow">Order conversion</p><h3>Convert quotation to order</h3></div></div><div className="form-grid form-grid-3"><label>Quotation<select required value={form.quote_id} onChange={(e) => setForm({ ...form, quote_id: e.target.value })}><option value="">Choose quotation</option>{quotes.map((quote) => <option key={quote.id} value={quote.database_id || quote.id}>{quote.id} · {quote.customer}</option>)}</select></label><label>Delivery date<input type="date" value={form.delivery_date} onChange={(e) => setForm({ ...form, delivery_date: e.target.value })} /></label><label>Notes<input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label></div>{error && <div className="form-error">{error}</div>}<button className="button">Create order</button></form>}
    <section className="order-grid">{orders.map((order) => <article className={`panel order-card ${selected?.id === order.id ? 'selected' : ''}`} key={order.id} onClick={() => setSelected(order)}><div className="panel-heading"><div><p className="eyebrow">{order.order_number} · {order.quote_number}</p><h3>{order.customer}</h3></div><span className="status status-approved">{order.status}</span></div><div className="order-status-grid"><label>Production<select disabled={!canManage} value={order.production_status} onChange={(e) => change(order.id, 'production_status', e.target.value)}><option>Not started</option><option>In production</option><option>Ready for delivery</option><option>Completed</option></select></label><label>Installation<select disabled={!canManage} value={order.installation_status} onChange={(e) => change(order.id, 'installation_status', e.target.value)}><option>Not scheduled</option><option>Scheduled</option><option>Installed</option></select></label></div><div className="order-meta"><span>₹{Number(order.amount || 0).toLocaleString('en-IN')}</span><span>{order.delivery_date || 'Delivery date pending'}</span></div></article>)}</section>
    {selected && <section className="panel history-panel"><div className="panel-heading"><div><p className="eyebrow">Project updates</p><h3>{selected.order_number}</h3></div><button className="text-button dark-text-button" onClick={() => setSelected(null)}>Close</button></div>{canManage && <form className="mini-form" onSubmit={addUpdate}><input placeholder="Add a production or delivery update" value={updateText} onChange={(e) => setUpdateText(e.target.value)} /><button className="button button-small">Add update</button></form>}<div className="history-list">{(selected.updates || []).map((item) => <div className="history-item" key={item.id}><strong>{item.author}</strong><span>{item.body}</span><small>{new Date(item.created_at).toLocaleString()}</small></div>)}</div></section>}
  </AppShell>
}
