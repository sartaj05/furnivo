import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createInventory, getInventory, getProducts, updateInventory } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const emptyForm = { product_id: '', quantity: 0, reserved_quantity: 0, reorder_level: 0, supplier: '', location: '' }

export default function InventoryPage() {
  const { user } = useAuth()
  const canEdit = ['admin', 'sales'].includes(user.role)
  const canCreate = user.role === 'admin'
  const [items, setItems] = useState([])
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  async function load() { setItems((await getInventory()).items || []); if (canCreate) setProducts((await getProducts()).items || []) }
  useEffect(() => { load() }, [])

  async function submit(event) { event.preventDefault(); setError(''); try { await createInventory(form); setForm(emptyForm); setShowForm(false); await load() } catch (err) { setError(err.message) } }
  async function edit(item, field, value) { await updateInventory(item.id, { [field]: value }); await load() }

  return <AppShell title="Inventory" eyebrow="Stock & availability" actions={canCreate && <button className="button button-small" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close' : 'Add stock item'}</button>}>
    {showForm && <form className="panel customer-editor" onSubmit={submit}><div className="panel-heading"><div><p className="eyebrow">Inventory setup</p><h3>Add product stock</h3></div></div><div className="form-grid form-grid-3"><label>Product<select required value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}><option value="">Choose product</option>{products.map((product) => <option value={product.id} key={product.id}>{product.name} · {product.sku}</option>)}</select></label><label>Quantity<input type="number" min="0" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} /></label><label>Reserved<input type="number" min="0" value={form.reserved_quantity} onChange={(e) => setForm({ ...form, reserved_quantity: e.target.value })} /></label><label>Reorder level<input type="number" min="0" value={form.reorder_level} onChange={(e) => setForm({ ...form, reorder_level: e.target.value })} /></label><label>Supplier<input value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} /></label><label>Location<input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /></label></div>{error && <div className="form-error">{error}</div>}<button className="button">Save stock item</button></form>}
    <section className="inventory-grid">{items.map((item) => <article className="panel inventory-card" key={item.id}><div className="panel-heading"><div><p className="eyebrow">{item.sku}</p><h3>{item.product}</h3><small>{item.variant || 'Standard item'}</small></div>{item.is_low_stock ? <span className="status status-rejected">Low stock</span> : <span className="status status-approved">Healthy</span>}</div><div className="inventory-numbers"><div><span>Available</span><strong>{Number(item.available_quantity || 0).toLocaleString('en-IN')}</strong></div><div><span>Total</span><strong>{Number(item.quantity || 0).toLocaleString('en-IN')}</strong></div><div><span>Reserved</span><strong>{Number(item.reserved_quantity || 0).toLocaleString('en-IN')}</strong></div></div>{canEdit ? <div className="inventory-edit-grid"><label>Quantity<input type="number" min="0" value={item.quantity} onChange={(e) => edit(item, 'quantity', e.target.value)} /></label><label>Reserved<input type="number" min="0" value={item.reserved_quantity} onChange={(e) => edit(item, 'reserved_quantity', e.target.value)} /></label><label>Reorder level<input type="number" min="0" value={item.reorder_level} onChange={(e) => edit(item, 'reorder_level', e.target.value)} /></label></div> : null}<div className="order-meta"><span>{item.supplier || 'Supplier not set'}</span><span>{item.location || 'Location not set'}</span></div></article>)}</section>
  </AppShell>
}
