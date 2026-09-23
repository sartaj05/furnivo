import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { createQuote, createQuotePreset, getCustomerPricing, getCustomers, getFurnitureConfigurationOptions, getFurnitureConfigurations, getProducts, getQuotePresets, saveCustomerPricing, saveFurnitureConfiguration } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const emptyLine = { product_id: '', variant_id: '', quantity: 1, options: { material: 'Oak', fabric: 'Performance fabric', color: 'Natural', finish: 'Matte' }, dimensions: {}, unit_price: 0, description: '', sku: '', unit: 'piece', image: '' }

export default function QuoteConfiguratorPage() {
  const { user } = useAuth()
  const [products, setProducts] = useState([])
  const [customers, setCustomers] = useState([])
  const [presets, setPresets] = useState([])
  const [savedConfigurations, setSavedConfigurations] = useState([])
  const [options, setOptions] = useState({ materials: [], fabrics: [], colors: [], finishes: [], dimension_surcharge_percent: 8 })
  const [customerId, setCustomerId] = useState('')
  const [configurationName, setConfigurationName] = useState('')
  const [pricing, setPricing] = useState({ tier: 'Standard', discount_percent: 0 })
  const [room, setRoom] = useState('')
  const [packageDiscount, setPackageDiscount] = useState(0)
  const [items, setItems] = useState([{ ...emptyLine }])
  const [presetName, setPresetName] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getProducts(), getCustomers(), getQuotePresets(), getFurnitureConfigurationOptions(), getFurnitureConfigurations()]).then(([productResult, customerResult, presetResult, optionResult, configurationResult]) => {
      setProducts(productResult.items || [])
      setCustomers(customerResult.items || [])
      setPresets(presetResult.items || [])
      setOptions(optionResult.options || options)
      setSavedConfigurations(configurationResult.items || [])
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

  function calculateLine(line) {
    const product = products.find((item) => Number(item.id) === Number(line.product_id))
    const variant = product?.variants?.find((item) => Number(item.id) === Number(line.variant_id))
    if (!product) return { ...line, unit_price: 0, line_total: 0 }
    const optionDelta = ['materials', 'fabrics', 'colors', 'finishes'].reduce((sum, group) => sum + Number(options[group]?.find((item) => item.value === line.options?.[group.slice(0, -1)])?.price_delta || 0), 0)
    const dimensions = line.dimensions || {}
    const defaults = { width: variant?.width_mm || '', height: variant?.height_mm || '', depth: variant?.depth_mm || '' }
    const customDimensions = Object.entries(dimensions).some(([key, value]) => value && Number(value) !== Number(defaults[key] || 0))
    const dimensionDelta = customDimensions ? Number(product.price || 0) * Number(options.dimension_surcharge_percent || 8) / 100 : 0
    const unitPrice = Math.max(0, Number(product.price || 0) + Number(variant?.price_delta || 0) + optionDelta + dimensionDelta)
    const dimensionLabel = ['width', 'height', 'depth'].filter((key) => dimensions[key]).map((key) => dimensions[key]).join(' x ')
    const optionLabel = Object.values(line.options || {}).filter(Boolean).join(', ')
    return { ...line, unit_price: Math.round(unitPrice * 100) / 100, line_total: Math.round(Number(line.quantity || 0) * unitPrice * 100) / 100, description: [product.name, optionLabel, dimensionLabel && `${dimensionLabel} mm`].filter(Boolean).join(' · '), sku: variant?.sku || product.sku, unit: product.unit, image: product.image }
  }

  function chooseProduct(index, value) {
    const product = products.find((item) => Number(item.id) === Number(value))
    const variant = product?.variants?.[0]
    const next = [...items]
    next[index] = calculateLine({ ...next[index], product_id: value, variant_id: variant?.id || '', dimensions: { width: variant?.width_mm || '', height: variant?.height_mm || '', depth: variant?.depth_mm || '' }, image: product?.image || '' })
    setItems(next)
  }

  function chooseVariant(index, value) {
    const line = items[index]
    const product = products.find((item) => Number(item.id) === Number(line.product_id))
    const variant = product?.variants?.find((item) => Number(item.id) === Number(value))
    setLine(index, { variant_id: value, dimensions: { width: variant?.width_mm || '', height: variant?.height_mm || '', depth: variant?.depth_mm || '' } })
  }

  function setLine(index, changes) { setItems(items.map((line, lineIndex) => lineIndex === index ? calculateLine({ ...line, ...changes, options: { ...line.options, ...(changes.options || {}) }, dimensions: { ...line.dimensions, ...(changes.dimensions || {}) } }) : line)) }

  function applyPreset(preset) {
    setRoom(preset.room || '')
    setPackageDiscount(Number(preset.discount_percent || 0))
    setItems((preset.items || []).map((item) => calculateLine({ ...emptyLine, ...item, options: { ...emptyLine.options, ...(item.options || {}) }, dimensions: item.dimensions || {} })))
    setMessage(`${preset.name} loaded. Adjust the visual selections and save it as a configuration.`)
  }

  function loadConfiguration(configuration) {
    setConfigurationName(configuration.name || '')
    setRoom(configuration.room || '')
    setCustomerId(configuration.customer_id || '')
    setItems((configuration.items || []).map((item) => calculateLine({ ...emptyLine, ...item, options: { ...emptyLine.options, ...(item.options || {}) }, dimensions: item.dimensions || {} })))
    setMessage(`${configuration.configuration_number} loaded for editing.`)
  }

  const totalDiscount = Math.min(100, Number(pricing.discount_percent || 0) + Number(packageDiscount || 0))
  const calculatedItems = useMemo(() => items.map(calculateLine), [items, products, options])
  const totals = useMemo(() => {
    const subtotal = calculatedItems.reduce((sum, item) => sum + Number(item.line_total || 0), 0)
    const discount = subtotal * totalDiscount / 100
    const tax = (subtotal - discount) * 18 / 100
    return { subtotal, discount, tax, total: subtotal - discount + tax }
  }, [calculatedItems, totalDiscount])

  async function persistConfiguration() {
    const customer = customers.find((item) => Number(item.id) === Number(customerId))
    if (!customer || !configurationName.trim() || calculatedItems.some((item) => !item.product_id)) throw new Error('Choose a customer, configuration name, and product for every line.')
    const result = await saveFurnitureConfiguration({ name: configurationName.trim(), room, customer_id: customer.id, items: calculatedItems.map(({ line_total, ...item }) => item) })
    setSavedConfigurations((current) => [result.item, ...current.filter((item) => item.id !== result.item.id)])
    return result.item
  }

  async function saveConfiguration(event, createQuoteAfter = false) {
    event?.preventDefault(); setError(''); setMessage('')
    try {
      const configuration = await persistConfiguration()
      if (createQuoteAfter) {
        const customer = customers.find((item) => Number(item.id) === Number(customerId))
        await createQuote({ configuration_id: configuration.id, customer_id: customer.id, customer: customer.company, notes: `${room || 'Custom'} furniture configuration ${configuration.configuration_number}.`, discount_percent: totalDiscount, tax_percent: 18, items: configuration.items })
        setMessage(`${configuration.configuration_number} saved and draft quotation created.`)
      } else setMessage(`${configuration.configuration_number} saved. Its selections are ready for production and inventory.`)
    } catch (err) { setError(err.message) }
  }

  async function savePreset() {
    setError(''); setMessage('')
    if (!presetName.trim() || items.some((item) => !item.product_id)) return setError('Add a preset name and choose a product for every line.')
    try {
      const result = await createQuotePreset({ name: presetName.trim(), kind: 'Reusable template', room, description: `${room || 'Custom'} package template`, discount_percent: packageDiscount, items: calculatedItems })
      setPresets([result.item, ...presets]); setPresetName(''); setMessage('Reusable quotation template saved.')
    } catch (err) { setError(err.message) }
  }

  return <AppShell title="Furniture visual configurator" eyebrow="Design, price & quote from one workspace" actions={<span className="mode-chip">Configurator MVP</span>}>
    <div className="configurator-layout">
      <section className="panel configurator-main">
        <div className="panel-heading"><div><p className="eyebrow">Build a project quote</p><h3>Configure the scope</h3></div><span className="status status-approved">{pricing.tier} tier · {pricing.discount_percent || 0}% customer discount</span></div>
        <form onSubmit={(event) => saveConfiguration(event, true)}>
          <div className="form-grid form-grid-3 configurator-fields">
            <label>Customer<select required value={customerId} onChange={(e) => chooseCustomer(e.target.value)}><option value="">Choose customer</option>{customers.map((item) => <option value={item.id} key={item.id}>{item.company}</option>)}</select></label>
            <label>Configuration name<input required value={configurationName} onChange={(e) => setConfigurationName(e.target.value)} placeholder="Villa living room set" /></label>
            <label>Room / project<input value={room} onChange={(e) => setRoom(e.target.value)} placeholder="Living room, office, villa" /></label>
            <label>Package discount %<input type="number" min="0" max="100" step="0.01" value={packageDiscount} onChange={(e) => setPackageDiscount(e.target.value)} /></label>
            <label>Customer pricing tier<select value={pricing.tier || 'Standard'} disabled={!customerId || user.role === 'designer'} onChange={(e) => setPricing({ ...pricing, tier: e.target.value })}><option>Standard</option><option>Silver</option><option>Gold</option><option>Platinum</option></select></label>
            <label>Customer discount %<input type="number" min="0" max="100" step="0.01" disabled={!customerId || user.role === 'designer'} value={pricing.discount_percent || 0} onChange={(e) => setPricing({ ...pricing, discount_percent: e.target.value })} /></label>
            {['admin', 'sales'].includes(user.role) && <button type="button" className="button button-ghost configurator-save-pricing" onClick={savePricing}>Save customer pricing</button>}
          </div>
          <div className="configurator-lines">
            {calculatedItems.map((line, index) => {
              const product = products.find((item) => Number(item.id) === Number(line.product_id))
              return <div className="visual-config-card configurator-line" key={index}>
                {line.image ? <img className="visual-config-preview" src={line.image} alt="" /> : <span className="visual-config-preview">Preview</span>}
                <label>Product<select required value={line.product_id} onChange={(e) => chooseProduct(index, e.target.value)}><option value="">Choose product</option>{products.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
                <label>Variant<select value={line.variant_id} onChange={(e) => chooseVariant(index, e.target.value)} disabled={!product?.variants?.length}><option value="">Standard</option>{(product?.variants || []).map((variant) => <option value={variant.id} key={variant.id}>{variant.finish}</option>)}</select></label>
                {['material', 'fabric', 'color', 'finish'].map((key) => <label key={key}>{key}<select value={line.options?.[key] || ''} onChange={(e) => setLine(index, { options: { [key]: e.target.value } })}><option value="">Choose {key}</option>{(options[`${key}s`] || []).map((item) => <option value={item.value} key={item.value}>{item.label}{item.price_delta ? ` (+INR ${item.price_delta})` : ''}</option>)}</select></label>)}
                {['width', 'height', 'depth'].map((key) => <label key={key}>{key} mm<input type="number" min="100" max="10000" step="1" value={line.dimensions?.[key] || ''} placeholder="Custom" onChange={(e) => setLine(index, { dimensions: { [key]: e.target.value } })} /></label>)}
                <label>Qty<input type="number" min="0.01" step="0.01" value={line.quantity} onChange={(e) => setLine(index, { quantity: e.target.value })} /></label>
                <label>Calculated price<input type="number" min="0" value={line.unit_price} readOnly /></label>
                <strong className="configurator-line-total">₹{(Number(line.quantity || 0) * Number(line.unit_price || 0)).toLocaleString('en-IN')}</strong>
                {items.length > 1 && <button type="button" className="button-link danger-link" onClick={() => setItems(items.filter((_, lineIndex) => lineIndex !== index))}>Remove</button>}
              </div>
            })}
          </div>
          <div className="configurator-actions"><button type="button" className="button button-ghost" onClick={() => setItems([...items, { ...emptyLine }])}>+ Add furniture item</button><div className="configurator-button-group"><button type="button" className="button button-ghost" onClick={() => saveConfiguration(null, false)}>Save configuration</button><button className="button">Save & create draft quote</button></div></div>
        </form>
        <div className="quote-total-box"><div><span>Subtotal</span><strong>₹{totals.subtotal.toLocaleString('en-IN')}</strong></div><div><span>Combined discount</span><strong>- ₹{totals.discount.toLocaleString('en-IN')}</strong></div><div><span>GST / tax</span><strong>₹{totals.tax.toLocaleString('en-IN')}</strong></div><div className="grand-total"><span>Estimated total</span><strong>₹{totals.total.toLocaleString('en-IN')}</strong></div></div>
        {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
      </section>
      <aside className="configurator-sidebar">
        <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Saved specifications</p><h3>Resume a configuration</h3></div></div><div className="preset-list">{savedConfigurations.map((configuration) => <button className="preset-card" key={configuration.id} onClick={() => loadConfiguration(configuration)}><span>{configuration.configuration_number} · {configuration.status}</span><strong>{configuration.name}</strong><small>{configuration.room || 'Flexible room'} · {configuration.items?.length || 0} items</small><b>INR {Number(configuration.subtotal || 0).toLocaleString('en-IN')}</b></button>)}{!savedConfigurations.length && <small className="muted-copy">Saved configurations will appear here.</small>}</div></section>
        <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Reusable catalog</p><h3>Packages & bundles</h3></div></div><div className="preset-list">{presets.map((preset) => <button className="preset-card" key={preset.id} onClick={() => applyPreset(preset)}><span>{preset.kind} · {preset.room || 'Flexible room'}</span><strong>{preset.name}</strong><small>{preset.description}</small><b>{preset.items?.length || 0} products · {preset.discount_percent || 0}% package discount</b></button>)}</div></section>
        <section className="panel"><p className="eyebrow">Save this configuration</p><h3>Reusable template</h3><input className="preset-name-input" value={presetName} onChange={(e) => setPresetName(e.target.value)} placeholder="e.g. 3BHK living room" /><button className="button button-small" onClick={savePreset}>Save template</button></section>
      </aside>
    </div>
  </AppShell>
}
