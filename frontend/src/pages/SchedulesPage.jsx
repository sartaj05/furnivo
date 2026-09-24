import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { confirmSchedule, createSchedule, getOrders, getSchedules, saveScheduleProof, signoffSchedule, updateSchedule } from '../lib/api'
import { useAuth } from '../context/AuthContext'

function LegacySchedulesPage() {
  const { user } = useAuth(); const canManage = ['admin', 'sales'].includes(user.role); const [items, setItems] = useState([]); const [orders, setOrders] = useState([]); const [showForm, setShowForm] = useState(false); const [form, setForm] = useState({ order_id: '', schedule_type: 'Delivery', scheduled_date: '', time_slot: 'Morning', assigned_team: '', proof_url: '', notes: '' }); const [error, setError] = useState('')
  async function load() { setItems((await getSchedules()).items || []); if (canManage) setOrders((await getOrders()).items || []) }
  useEffect(() => { load() }, [])
  async function submit(e) { e.preventDefault(); try { await createSchedule(form); setShowForm(false); await load() } catch (err) { setError(err.message) } }
  async function update(item, field, value) { await updateSchedule(item.id, { [field]: value }); await load() }
  return <AppShell title="Delivery & installation" eyebrow="Field scheduling" actions={canManage && <button className="button button-small" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close' : 'Schedule visit'}</button>}>
    {showForm && <form className="panel customer-editor" onSubmit={submit}><div className="panel-heading"><h3>Schedule delivery or installation</h3></div><div className="form-grid form-grid-3"><label>Order<select required value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })}><option value="">Choose order</option>{orders.map((item) => <option value={item.id} key={item.id}>{item.order_number} · {item.customer}</option>)}</select></label><label>Type<select value={form.schedule_type} onChange={(e) => setForm({ ...form, schedule_type: e.target.value })}><option>Delivery</option><option>Installation</option></select></label><label>Date<input required type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} /></label><label>Time slot<input value={form.time_slot} onChange={(e) => setForm({ ...form, time_slot: e.target.value })} /></label><label>Assigned team<input value={form.assigned_team} onChange={(e) => setForm({ ...form, assigned_team: e.target.value })} /></label><label>Proof URL<input value={form.proof_url} onChange={(e) => setForm({ ...form, proof_url: e.target.value })} /></label></div>{error && <div className="form-error">{error}</div>}<button className="button">Save schedule</button></form>}
    <section className="schedule-grid">{items.map((item) => <article className="panel schedule-card" key={item.id}><div className="panel-heading"><div><p className="eyebrow">{item.schedule_type} · {item.order_number}</p><h3>{item.customer}</h3></div><span className="status status-approved">{item.status}</span></div><div className="schedule-date"><strong>{item.scheduled_date}</strong><span>{item.time_slot}</span></div><p>{item.assigned_team || 'Team not assigned'}</p>{canManage ? <div className="order-meta"><select value={item.status} onChange={(e) => update(item, 'status', e.target.value)}><option>Scheduled</option><option>In progress</option><option>Completed</option><option>Cancelled</option></select>{item.proof_url && <a className="button-link" href={item.proof_url} target="_blank" rel="noreferrer">View proof</a>}</div> : item.proof_url && <a className="button-link" href={item.proof_url} target="_blank" rel="noreferrer">View completion proof</a>}</article>)}</section>
  </AppShell>
}

function DeliveryExecutionPanel() {
  const [items, setItems] = useState([]); const [signatures, setSignatures] = useState({}); const [message, setMessage] = useState('')
  async function load() { setItems((await getSchedules()).items || []) }
  useEffect(() => { load() }, [])
  async function confirm(item) { await confirmSchedule(item.id); setMessage('Customer confirmation saved.'); await load() }
  async function complete(item) { await saveScheduleProof(item.id, { proof_url: item.proof_url || 'demo://delivery-proof', notes: 'Completion proof captured from delivery console.' }); setMessage('Delivery proof saved and schedule completed.'); await load() }
  async function signoff(item) { const signature = (signatures[item.id] || '').trim(); try { const result = await signoffSchedule(item.id, { signature, accepted: true }); setItems((current) => current.map((entry) => entry.id === item.id ? result.item : entry)); setMessage(`Customer sign-off saved for ${item.order_number}.`) } catch (error) { setMessage(error.message) } }
  return <section className="panel delivery-execution-panel"><div className="panel-heading"><div><p className="eyebrow">Live delivery board</p><h3>ETA, confirmation & proof</h3></div></div><div className="schedule-grid">{items.map((item) => <article className="schedule-card" key={item.id}><strong>{item.order_number} · {item.schedule_type}</strong><p>{item.customer} · {item.eta || item.time_slot}</p><div className="order-meta"><span>{item.customer_confirmed ? 'Customer confirmed' : 'Awaiting confirmation'}</span><button className="button-link" onClick={() => confirm(item)}>Confirm</button><button className="button-link" onClick={() => complete(item)}>Complete with proof</button></div></article>)}</div>{message && <div className="success-message">{message}</div>}</section>
}

function SignoffPanel() {
  const [items, setItems] = useState([]); const [signatures, setSignatures] = useState({}); const [message, setMessage] = useState('')
  useEffect(() => { getSchedules().then((result) => setItems(result.items || [])) }, [])
  async function signoff(item) { try { const result = await signoffSchedule(item.id, { signature: signatures[item.id] || '', accepted: true }); setItems((current) => current.map((entry) => entry.id === item.id ? result.item : entry)); setMessage(`Sign-off saved for ${item.order_number}.`) } catch (error) { setMessage(error.message) } }
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Customer sign-off</p><h3>Delivery and installation acceptance</h3></div></div>{items.map((item) => <div className="order-meta" key={item.id}><span><strong>{item.order_number} · {item.schedule_type}</strong><small>{item.customer} · {item.status}</small></span><input placeholder="Customer name/signature" value={signatures[item.id] || ''} onChange={(event) => setSignatures({ ...signatures, [item.id]: event.target.value })} /><button className="button button-small" onClick={() => signoff(item)}>Sign off</button></div>)}{message && <div className="success-message">{message}</div>}</section>
}

export default function SchedulesPage() { return <><LegacySchedulesPage /><DeliveryExecutionPanel /><SignoffPanel /></> }
