import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { broadcastNotification, getNotificationDeliverySummary, getNotificationProviderStatus } from '../lib/api'
import '../styles/notification-providers.css'

export default function NotificationAutomationEnhancedPage() {
  const [form, setForm] = useState({ title: '', body: '', channel: 'in_app' }); const [summary, setSummary] = useState({}); const [providers, setProviders] = useState(null); const [message, setMessage] = useState(''); const [error, setError] = useState('')
  async function load() { const [summaryResult, providerResult] = await Promise.all([getNotificationDeliverySummary(), getNotificationProviderStatus()]); setSummary(summaryResult.summary || {}); setProviders(providerResult) }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  async function submit(event) { event.preventDefault(); setError(''); try { const result = await broadcastNotification(form); setMessage(`${result.items?.length || 0} recipient(s) notified.`); setForm({ ...form, title: '', body: '' }); await load() } catch (err) { setError(err.message) } }
  return <AppShell title="Notification automation" eyebrow="Email, WhatsApp, SMS & in-app communications">
    {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
    <section className="panel provider-grid"><div className="panel-heading"><div><p className="eyebrow">Provider readiness</p><h3>Delivery channels</h3></div><span className="mode-chip">{providers?.mode || 'loading'}</span></div>{Object.entries(providers?.channels || {}).map(([channel, item]) => <div className="provider-row" key={channel}><span><strong>{channel.replace('_', ' ')}</strong><small>{item.provider}</small></span><b className={item.configured ? 'check-good' : 'check-warning'}>{item.configured ? 'Ready' : 'Configure'}</b></div>)}</section>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Broadcast</p><h3>Send an operational update</h3></div></div><form className="service-form" onSubmit={submit}><label>Title<input required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label><label>Message<textarea required rows="4" value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} /></label><label>Channel<select value={form.channel} onChange={(event) => setForm({ ...form, channel: event.target.value })}><option value="in_app">In-app</option><option value="email">Email</option><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option></select></label><button className="button">Send notification</button></form></section>
    <section className="metrics-grid"><article className="metric-card"><span>Sent</span><strong>{summary.sent || 0}</strong></article><article className="metric-card"><span>Pending</span><strong>{summary.pending || 0}</strong></article><article className="metric-card"><span>Provider setup needed</span><strong>{summary.pending_configuration || 0}</strong></article></section>
  </AppShell>
}
