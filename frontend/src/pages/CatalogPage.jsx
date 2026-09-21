import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'
import { createProduct, deleteProduct, getProducts, updateProduct } from '../lib/api'

const blankProduct = {
  sku: '', name: '', category: 'Furniture', price: '', unit: 'piece', material: '', description: '', image: '',
}

export default function CatalogPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState([])
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [mode, setMode] = useState('')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(blankProduct)
  const [error, setError] = useState('')

  const canManage = user.role === 'admin'

  async function load() {
    const result = await getProducts()
    setProducts(result.items)
    setMode(result.mode || 'api')
  }

  useEffect(() => { load() }, [])

  const categories = ['All', ...new Set(products.map((item) => item.category))]
  const filtered = useMemo(() => products.filter((item) => {
    const searchMatch = `${item.name} ${item.sku} ${item.material}`.toLowerCase().includes(query.toLowerCase())
    return searchMatch && (category === 'All' || item.category === category)
  }), [products, query, category])

  function startCreate() {
    setEditing('new')
    setForm(blankProduct)
    setError('')
  }

  function startEdit(product) {
    setEditing(product.id)
    setForm({ ...blankProduct, ...product, price: String(product.price) })
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      if (editing === 'new') await createProduct(form)
      else await updateProduct(editing, form)
      setEditing(null)
      setForm(blankProduct)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  async function remove(product) {
    if (!window.confirm(`Archive ${product.name}?`)) return
    await deleteProduct(product.id)
    await load()
  }

  return (
    <AppShell
      title="Product catalog"
      eyebrow="Commercial library"
      actions={canManage ? <button className="button button-small" onClick={startCreate}>Add product</button> : <span className="mode-chip">{mode === 'demo' ? 'Local demo data' : 'Live catalog'}</span>}
    >
      {editing && (
        <form className="catalog-editor panel" onSubmit={submit}>
          <div className="panel-heading"><div><p className="eyebrow">Catalog admin</p><h3>{editing === 'new' ? 'Create product' : 'Edit product'}</h3></div><button type="button" className="text-button dark-text-button" onClick={() => setEditing(null)}>Close</button></div>
          <div className="form-grid form-grid-3">
            <label>SKU<input required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} /></label>
            <label>Product name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label>Category<select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}><option>Furniture</option><option>Interiors</option><option>Building Material</option></select></label>
            <label>Price<input required type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></label>
            <label>Unit<input value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} /></label>
            <label>Material<input value={form.material} onChange={(e) => setForm({ ...form, material: e.target.value })} /></label>
            <label className="form-span-3">Image URL<input value={form.image} onChange={(e) => setForm({ ...form, image: e.target.value })} placeholder="https://…" /></label>
            <label className="form-span-3">Description<textarea rows="3" value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          </div>
          {error && <div className="form-error">{error}</div>}
          <button className="button">{editing === 'new' ? 'Create product' : 'Save changes'}</button>
        </form>
      )}

      <div className="toolbar">
        <input className="search-input" placeholder="Search name, SKU or material…" value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="filter-row">
          {categories.map((item) => <button className={category === item ? 'filter-chip active' : 'filter-chip'} key={item} onClick={() => setCategory(item)}>{item}</button>)}
        </div>
      </div>

      <section className="product-grid">
        {filtered.map((product) => (
          <article className="product-card" key={product.id}>
            <div className="product-image">
              {product.image ? <img src={product.image} alt={product.name} /> : <div className="image-placeholder">No image</div>}
              <span>{product.category}</span>
            </div>
            <div className="product-body">
              <small>{product.sku}</small><h3>{product.name}</h3><p>{product.material}</p>
              <div className="product-price"><strong>₹{Number(product.price).toLocaleString('en-IN')}</strong><span>/ {product.unit}</span></div>
              {canManage && <div className="card-actions"><button className="button-link" onClick={() => startEdit(product)}>Edit</button><button className="button-link danger-link" onClick={() => remove(product)}>Archive</button></div>}
            </div>
          </article>
        ))}
      </section>
    </AppShell>
  )
}
