import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getAnalytics, getAutomationTemplates, getBusinessPlanning, previewAutomation, reservePlanningStock, sendAutomation } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const money = (value) => `INR ${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function BusinessControlPage() {
  const { user } = useAuth()
  const [planning, setPlanning] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [templates, setTemplates] = useState([])
  const [event, setEvent] = useState('production_update')
  const [channel, setChannel] = useState('in_app')
  const [preview, setPreview] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function load() {
    const [planningResult, analyticsResult, automationResult] = await Promise.all([getBusinessPlanning(), getAnalytics(), getAutomationTemplates()])
    setPlanning(planningResult.planning || {})
    setAnalytics(analyticsResult)
    setTemplates(automationResult.templates || [])
  }

  useEffect(() => { load().catch((err) => setError(err.message)) }, [])

  async function reserve() {
    try { const result = await reservePlanningStock(); setPlanning(result.planning); setMessage(result.reserved?.length ? `${result.reserved.length} material reservations created.` : 'All required stock is already reserved or available.') } catch (err) { setError(err.message) }
  }

  async function showPreview() {
    try { setPreview((await previewAutomation({ event, variables: { quote_number: 'Q-1042', customer: 'Northline Studio', order_number: 'ORD-1001', status: 'Assembly', delivery_date: '2026-10-18', ticket_number: 'SVC-8001' } })).preview) } catch (err) { setError(err.message) }
  }

  async function send() {
    try { await sendAutomation({ event, channel, user_id: user.id, recipient: user.email, variables: { quote_number: 'Q-1042', customer: 'Northline Studio', order_number: 'ORD-1001', status: 'Assembly', delivery_date: '2026-10-18', ticket_number: 'SVC-8001' } }); setMessage(`${templates.find((item) => item.event === event)?.label || 'Automation'} sent in ${channel} mode.`) } catch (err) { setError(err.message) }
  }

  if (error && !planning) return <AppShell title="Business control center" eyebrow="Planning, margins & communication"><div className="form-error">{error}</div></AppShell>
  if (!planning || !analytics) return <AppShell title="Business control center" eyebrow="Planning, margins & communication"><p className="muted-copy">Loading business controls…</p></AppShell>
  const summary = planning.summary || {}; const profit = analytics.profitability || {}
  return <AppShell title="Business control center" eyebrow="Planning, margins & communication" actions={<span className="mode-chip">MVP controls</span>}>
    <section className="control-metrics">{[['Estimated production cost', money(summary.estimated_cost)], ['Material cost', money(summary.material_cost)], ['Gross profit', money(profit.gross_profit)], ['Gross margin', `${profit.margin_percent || 0}%`], ['Shortages', summary.shortages || 0], ['Low stock', summary.low_stock_items || 0]].map(([label, value]) => <article className="panel control-metric" key={label}><p className="eyebrow">{label}</p><strong>{value}</strong></article>)}</section>
    <div className="control-grid"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Inventory + production</p><h3>Material requirements</h3></div><button className="button button-small" onClick={reserve}>Reserve available stock</button></div>{planning.materials?.length ? planning.materials.map((item) => <div className="control-row" key={`${item.job_number}-${item.id}`}><span><strong>{item.product}</strong><small>{item.job_number} · {item.required_quantity} {item.unit} required · {item.location || 'No location'}</small></span><span className={item.shortage_quantity > 0 ? 'control-warning' : 'control-good'}>{item.shortage_quantity > 0 ? `${item.shortage_quantity} short` : 'Covered'}<small>{money(item.total_cost)} estimated</small></span></div>) : <p className="muted-copy">Create a production job with BOM materials to see planning requirements.</p>}{planning.purchase_suggestions?.length ? <><h4>Purchase-order suggestions</h4>{planning.purchase_suggestions.map((item) => <div className="control-row" key={`${item.product}-${item.supplier}`}><span><strong>{item.product}</strong><small>{item.supplier} · jobs {item.jobs.join(', ')}</small></span><strong>{item.quantity.toFixed(2)} · {money(item.estimated_total)}</strong></div>)}</> : <p className="muted-copy">No purchase suggestions. Current BOM materials are covered.</p>}</section>
      <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Profitability</p><h3>Project contribution</h3></div></div>{profit.projects?.length ? profit.projects.map((item) => <div className="control-row" key={item.order_number}><span><strong>{item.order_number} · {item.customer}</strong><small>{money(item.revenue)} revenue · {money(item.estimated_cost)} estimated cost</small></span><span className="control-good">{money(item.gross_profit)}<small>{item.margin_percent}% margin</small></span></div>) : <p className="muted-copy">Approved orders will appear here with estimated material and labor costs.</p>}<h4>Costing model</h4><p className="muted-copy">BOM quantities include wastage. Material cost uses saved unit cost or product cost price, with an 18% labor estimate when labor is not entered.</p></section></div>
    <section className="panel automation-panel"><div className="panel-heading"><div><p className="eyebrow">Email + WhatsApp automation</p><h3>Message templates</h3></div></div><div className="form-grid form-grid-3"><label>Event<select value={event} onChange={(e) => { setEvent(e.target.value); setPreview(null) }}>{templates.map((item) => <option value={item.event} key={item.event}>{item.label}</option>)}</select></label><label>Channel<select value={channel} onChange={(e) => setChannel(e.target.value)}><option value="in_app">In-app</option><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select></label><div className="automation-actions"><button className="button button-ghost" onClick={showPreview}>Preview message</button><button className="button" onClick={send}>Send test to me</button></div></div>{preview && <div className="automation-preview"><strong>{preview.title}</strong><p>{preview.body}</p><small>Available channels: {preview.channels.join(', ')}</small></div>}{(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}</section>
  </AppShell>
}
