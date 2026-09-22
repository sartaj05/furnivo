import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { createQuote, createQuotePreset, getCustomerPricing, getCustomers, getProducts, getQuotePresets, saveCustomerPricing } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const emptyLine = { product_id: '', variant_id: '', quantity: 1, unit_price: 0, description: '', sku: '', unit: 'piece' }

export default function QuoteConfiguratorPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState([])
  const [customers, setCustomers] = useState([])
  const [presets, setPresets] = useState([])
  const [customerId, setCustomerId] = useState('')
  const [pricing, setPricing] = useState({ tier: 'Standard', discount_percent: 0 })
  const [room, setRoom] = useState('')
  const [packageDiscount, setPackageDiscount] = useState(0)
  const [items, setItems] = useState([{ ...emptyLine }])
  const [presetName, setPresetName] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getProducts(), getCustomers(), getQuotePresets()]).then(([productResult, customerResult, presetResult]) => {
      setProducts(productResult.items || [])
      setCustomers(customerResult.items || [])
      setPresets(presetResult.items || [])
    }).catch((err) => setError(err.message))
  }, [])

  async function chooseCustomer(value) {
    setCustomerId(value)
    if (!value) return setPricing({ tier: 'Standard', discount_percent: 0 })
    try { setPricing((await getCustomerPricing(value)).item || { tier: 'Standard', discount_percent: 0 }) } catch (err) { setError(err.message) }
  }

  async function savePricing() {
    if (!customerId) return setError('Choose a customer before saving pricing.')
    try { await saveCustomerPricing(customerId, { tier: pricing.tier, discount_percent: pricing.discount_percent }); setMessage('Customer pricing tier saved.') } catch (err) { setError(err.message) }
  }

  function chooseProduct(index, value) {
    const product = products.find((item) => Number(item.id) === Number(value))
    const next = [...items]
    next[index] = { ...next[index], product_id: value, variant_id: '', unit_price: product?.price || 0, description: product?.name || '', sku: product?.sku || '', unit: product?.unit || 'piece' }
    setItems(next)
  }

  function chooseVariant(index, value) {
    const next = [...items]
    const product = products.find((item) => Number(item.id) === Number(next[index].product_id))
    const variant = product?.variants?.find((item) => Number(item.id) === Number(value))
    next[index] = { ...next[index], variant_id: value, unit_price: Number(product?.price || 0) + Number(variant?.price_delta || 0), sku: variant?.sku || product?.sku || '' }
    setItems(next)
  }

  function setLine(index, changes) { setItems(items.map((line, lineIndex) => lineIndex === index ? { ...line, ...changes } : line)) }

  function applyPreset(preset) {
    setRoom(preset.room || '')
    setPackageDiscount(Number(preset.discount_percent || 0))
    setItems((preset.items || []).map((item) => ({ ...emptyLine, ...item })))
    setMessage(`${preset.name} loaded. Adjust quantities and save as a draft quote.`)
  }

  const totalDiscount = Math.min(100, Number(pricing.discount_percent || 0) + Number(packageDiscount || 0))
  const totals = useMemo(() => {
    const subtotal = items.reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0)
    const discount = subtotal * totalDiscount / 100
    const tax = (subtotal - discount) * 18 / 100
    return { subtotal, discount, tax, total: subtotal - discount + tax }
  }, [items, totalDiscount])

  async function saveQuote(event) {
    event.preventDefault(); setError(''); setMessage('')
    const customer = customers.find((item) => Number(item.id) === Number(customerId))
    if (!customer || items.some((item) => !item.product_id)) return setError('Choose a customer and a product for every line.')
    try {
      await createQuote({ customer_id: customer.id, customer: customer.company, notes: `${room || 'Custom'} package configured in quotation studio.`, discount_percent: totalDiscount, tax_percent: 18, items })
      setMessage('Draft quote created successfully. Open Quotations to review and send it.')
    } catch (err) { setError(err.message) }
  }

  async function savePreset() {
    setError(''); setMessage('')
    if (!presetName.trim() || items.some((item) => !item.product_id)) return setError('Add a preset name and choose a product for every line.')
    try {
      const result = await createQuotePreset({ name: presetName.trim(), kind: 'Reusable template', room, description: `${room || 'Custom'} package template`, discount_percent: packageDiscount, items })
      setPresets([result.item, ...presets]); setPresetName(''); setMessage('Reusable quotation template saved.')
    } catch (err) { setError(err.message) }
  }

  return <AppShell title="Quotation configurator" eyebrow="Packages, tiers & reusable templates" actions={<span className="mode-chip">Studio</span>}>
    <div className="configurator-layout">
      <section className="panel configurator-main">
        <div className="panel-heading"><div><p className="eyebrow">Build a project quote</p><h3>Configure the scope</h3></div><span className="status status-approved">{pricing.tier} tier · {pricing.discount_percent || 0}% customer discount</span></div>
        <form onSubmit={saveQuote}>
          <div className="form-grid form-grid-3 configurator-fields">
            <label>Customer<select required value={customerId} onChange={(e) => chooseCustomer(e.target.value)}><option value="">Choose customer</option>{customers.map((item) => <option value={item.id} key={item.id}>{item.company}</option>)}</select></label>
            <label>Room / project package<input value={room} onChange={(e) => setRoom(e.target.value)} placeholder="Living room, office, villa" /></label>
            <label>Package discount %<input type="number" min="0" max="100" step="0.01" value={packageDiscount} onChange={(e) => setPackageDiscount(e.target.value)} /></label>
            <label>Customer pricing tier<select value={pricing.tier || 'Standard'} disabled={!customerId || user.role === 'designer'} onChange={(e) => setPricing({ ...pricing, tier: e.target.value })}><option>Standard</option><option>Silver</option><option>Gold</option><option>Platinum</option></select></label>
            <label>Customer discount %<input type="number" min="0" max="100" step="0.01" disabled={!customerId || user.role === 'designer'} value={pricing.discount_percent || 0} onChange={(e) => setPricing({ ...pricing, discount_percent: e.target.value })} /></label>
            {['admin', 'sales'].includes(user.role) && <button type="button" className="button button-ghost configurator-save-pricing" onClick={savePricing}>Save customer pricing</button>}
          </div>
          <div className="configurator-lines">
            {items.map((line, index) => {
              const product = products.find((item) => Number(item.id) === Number(line.product_id))
              return <div className="configurator-line" key={index}>
                <label>Product<select required value={line.product_id} onChange={(e) => chooseProduct(index, e.target.value)}><option value="">Choose product</option>{products.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
                <label>Variant<select value={line.variant_id} onChange={(e) => chooseVariant(index, e.target.value)} disabled={!product?.variants?.length}><option value="">Standard</option>{(product?.variants || []).map((variant) => <option value={variant.id} key={variant.id}>{variant.finish}</option>)}</select></label>
                <label>Qty<input type="number" min="0.01" step="0.01" value={line.quantity} onChange={(e) => setLine(index, { quantity: e.target.value })} /></label>
                <label>Unit price<input type="number" min="0" value={line.unit_price} onChange={(e) => setLine(index, { unit_price: e.target.value })} /></label>
                <strong className="configurator-line-total">₹{(Number(line.quantity || 0) * Number(line.unit_price || 0)).toLocaleString('en-IN')}</strong>
                {items.length > 1 && <button type="button" className="button-link danger-link" onClick={() => setItems(items.filter((_, lineIndex) => lineIndex !== index))}>Remove</button>}
              </div>
            })}
          </div>
          <div className="configurator-actions"><button type="button" className="button button-ghost" onClick={() => setItems([...items, { ...emptyLine }])}>+ Add product</button><button className="button">Create draft quote</button></div>
        </form>
        <div className="quote-total-box"><div><span>Subtotal</span><strong>₹{totals.subtotal.toLocaleString('en-IN')}</strong></div><div><span>Combined discount</span><strong>- ₹{totals.discount.toLocaleString('en-IN')}</strong></div><div><span>GST / tax</span><strong>₹{totals.tax.toLocaleString('en-IN')}</strong></div><div className="grand-total"><span>Estimated total</span><strong>₹{totals.total.toLocaleString('en-IN')}</strong></div></div>
        {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
      </section>
      <aside className="configurator-sidebar">
        <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Reusable catalog</p><h3>Packages & bundles</h3></div></div><div className="preset-list">{presets.map((preset) => <button className="preset-card" key={preset.id} onClick={() => applyPreset(preset)}><span>{preset.kind} · {preset.room || 'Flexible room'}</span><strong>{preset.name}</strong><small>{preset.description}</small><b>{preset.items?.length || 0} products · {preset.discount_percent || 0}% package discount</b></button>)}</div></section>
        <section className="panel"><p className="eyebrow">Save this configuration</p><h3>Reusable template</h3><input className="preset-name-input" value={presetName} onChange={(e) => setPresetName(e.target.value)} placeholder="e.g. 3BHK living room" /><button className="button button-small" onClick={savePreset}>Save template</button></section>
      </aside>
    </div>
  </AppShell>
}
