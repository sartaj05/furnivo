import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'
import { createQuote, downloadQuotePdf, getCustomers, getProducts, getQuotes, updateQuoteStatus } from '../lib/api'

const emptyLine = () => ({ product_id: '', variant_id: '', description: '', sku: '', quantity: 1, unit: 'piece', unit_price: 0 })

export default function QuotesPage() {
  const { user } = useAuth()
  const [quotes, setQuotes] = useState([])
  const [products, setProducts] = useState([])
  const [customers, setCustomers] = useState([])
  const [form, setForm] = useState({ customer_id: '', customer: '', notes: '', discount_percent: 0, tax_percent: 18, shipping_amount: 0, items: [emptyLine()] })
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    const [quoteResult, productResult, customerResult] = await Promise.all([getQuotes(), getProducts(), getCustomers().catch(() => ({ items: [] }))])
    setQuotes(quoteResult.items)
    setProducts(productResult.items)
    setCustomers(customerResult.items)
  }

  useEffect(() => { load() }, [])

  const totals = useMemo(() => {
    const subtotal = form.items.reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0)
    const discount = subtotal * Number(form.discount_percent || 0) / 100
    const taxable = Math.max(subtotal - discount, 0)
    const tax = taxable * Number(form.tax_percent || 0) / 100
    const shipping = Number(form.shipping_amount || 0)
    return { subtotal, discount, tax, shipping, total: taxable + tax + shipping }
  }, [form])

  function setLine(index, patch) {
    setForm((current) => ({ ...current, items: current.items.map((item, i) => i === index ? { ...item, ...patch } : item) }))
  }

  function chooseProduct(index, productId) {
    const product = products.find((item) => Number(item.id) === Number(productId))
    if (!product) return setLine(index, { product_id: '', description: '', sku: '', unit_price: 0 })
    setLine(index, { product_id: product.id, variant_id: '', description: product.name, sku: product.sku, unit: product.unit, unit_price: product.price })
  }

  function chooseVariant(index, variantId) {
    const line = form.items[index]
    const product = products.find((item) => Number(item.id) === Number(line.product_id))
    const variant = (product?.variants || []).find((item) => Number(item.id) === Number(variantId))
    setLine(index, { variant_id: variant?.id || '', sku: variant?.sku || product?.sku || '', unit_price: Number(product?.price || 0) + Number(variant?.price_delta || 0) })
  }

  function addLine() { setForm((current) => ({ ...current, items: [...current.items, emptyLine()] })) }
  function removeLine(index) { setForm((current) => ({ ...current, items: current.items.filter((_, i) => i !== index) })) }

  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      await createQuote(form)
      setForm({ customer_id: '', customer: '', notes: '', discount_percent: 0, tax_percent: 18, shipping_amount: 0, items: [emptyLine()] })
      setShowForm(false)
      await load()
    } catch (err) { setError(err.message) }
  }

  async function changeStatus(quote, status) {
    await updateQuoteStatus(quote.database_id || quote.id, status)
    await load()
  }

  return (
    <AppShell title="Quotations" eyebrow="Commercial documents" actions={<button className="button button-small" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close' : 'New quotation'}</button>}>
      {showForm && (
        <form className="quote-builder panel" onSubmit={submit}>
          <div className="panel-heading"><div><p className="eyebrow">Quote builder</p><h3>Create a line-item quotation</h3></div><strong>₹{totals.total.toLocaleString('en-IN')}</strong></div>
          <div className="form-grid quote-head-fields">
            <label>Customer / studio<select required value={form.customer_id || form.customer} onChange={(e) => { const customer = customers.find((item) => String(item.id) === e.target.value); setForm({ ...form, customer_id: customer?.id || '', customer: customer?.company || e.target.value }) }}><option value="">Choose customer</option>{customers.map((customer) => <option value={customer.id} key={customer.id}>{customer.company}</option>)}</select></label>
            <label>Internal / customer notes<input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Delivery, scope, validity…" /></label>
          </div>
          <div className="quote-commercials">
            <label>Discount %<input type="number" min="0" max="100" step="0.01" value={form.discount_percent} onChange={(e) => setForm({ ...form, discount_percent: e.target.value })} /></label>
            <label>Tax / GST %<input type="number" min="0" max="100" step="0.01" value={form.tax_percent} onChange={(e) => setForm({ ...form, tax_percent: e.target.value })} /></label>
            <label>Shipping / handling<input type="number" min="0" step="0.01" value={form.shipping_amount} onChange={(e) => setForm({ ...form, shipping_amount: e.target.value })} /></label>
          </div>
          <div className="quote-lines">
            {form.items.map((line, index) => {
              const product = products.find((item) => Number(item.id) === Number(line.product_id))
              return <div className="quote-line" key={index}>
                <label>Product<select required value={line.product_id} onChange={(e) => chooseProduct(index, e.target.value)}><option value="">Choose product</option>{products.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.sku}</option>)}</select></label>
                <label>Variant<select value={line.variant_id} onChange={(e) => chooseVariant(index, e.target.value)} disabled={!product?.variants?.length}><option value="">Standard</option>{(product?.variants || []).map((variant) => <option value={variant.id} key={variant.id}>{variant.finish}</option>)}</select></label>
                <label>Qty<input required type="number" min="0.01" step="0.01" value={line.quantity} onChange={(e) => setLine(index, { quantity: e.target.value })} /></label>
                <label>Unit price<input required type="number" min="0" value={line.unit_price} onChange={(e) => setLine(index, { unit_price: e.target.value })} /></label>
                <div className="line-total"><span>Line total</span><strong>₹{(Number(line.quantity || 0) * Number(line.unit_price || 0)).toLocaleString('en-IN')}</strong></div>
                {form.items.length > 1 && <button type="button" className="button-link danger-link quote-remove" onClick={() => removeLine(index)}>Remove</button>}
              </div>
            })}
          </div>
          <div className="quote-total-box"><div><span>Subtotal</span><strong>₹{totals.subtotal.toLocaleString('en-IN')}</strong></div><div><span>Discount</span><strong>- ₹{totals.discount.toLocaleString('en-IN')}</strong></div><div><span>Tax</span><strong>₹{totals.tax.toLocaleString('en-IN')}</strong></div><div><span>Shipping</span><strong>₹{totals.shipping.toLocaleString('en-IN')}</strong></div><div className="grand-total"><span>Grand total</span><strong>₹{totals.total.toLocaleString('en-IN')}</strong></div></div>
          <div className="quote-builder-actions"><button type="button" className="button button-ghost" onClick={addLine}>+ Add line</button><button className="button">Save draft</button></div>
          {error && <div className="form-error">{error}</div>}
        </form>
      )}

      <section className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>Quote</th><th>Customer</th><th>Lines</th><th>Date</th><th>Status</th><th className="align-right">Amount</th><th>PDF</th></tr></thead><tbody>{quotes.map((quote) => <tr key={quote.id}><td data-label="Quote"><strong>{quote.id}</strong></td><td data-label="Customer">{quote.customer}</td><td data-label="Lines">{quote.items?.length || '—'}</td><td data-label="Date">{quote.date}</td><td data-label="Status">{user.role === 'admin' || user.role === 'sales' ? <select className="status-select" value={quote.status} onChange={(e) => changeStatus(quote, e.target.value)}><option>Draft</option><option>Sent</option><option>Approved</option><option>Rejected</option></select> : <span className={`status status-${quote.status.toLowerCase()}`}>{quote.status}</span>}</td><td data-label="Amount" className="align-right">₹{Number(quote.amount).toLocaleString('en-IN')}</td><td data-label="PDF"><button className="button-link" onClick={() => downloadQuotePdf(quote)}>Download</button></td></tr>)}</tbody></table></div></section>
    </AppShell>
  )
}
