import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getAccountingSummary, getPaymentProviderStatus, sendPaymentReminders } from '../lib/api'

export default function AccountingCenterPage() {
  const [data, setData] = useState({ summary: {}, overdue: [] })
  const [provider, setProvider] = useState(null)
  const [message, setMessage] = useState('')

  async function load() {
    const [summary, providerData] = await Promise.all([getAccountingSummary(), getPaymentProviderStatus()])
    setData(summary)
    setProvider(providerData.provider)
  }

  useEffect(() => { load() }, [])

  async function remind() {
    const result = await sendPaymentReminders()
    setMessage(`${result.sent || 0} payment reminder(s) generated.`)
    await load()
  }

  const summary = data.summary || {}
  return <AppShell title="Accounting control center" eyebrow="GST, reconciliation & collections">
    <section className="metrics-grid">
      <article className="metric-card"><span>Invoiced</span><strong>₹{Number(summary.invoiced || 0).toLocaleString('en-IN')}</strong></article>
      <article className="metric-card"><span>Collected</span><strong>₹{Number(summary.collected || 0).toLocaleString('en-IN')}</strong></article>
      <article className="metric-card"><span>Outstanding</span><strong>₹{Number(summary.outstanding || 0).toLocaleString('en-IN')}</strong></article>
      <article className="metric-card"><span>Overdue</span><strong>{summary.overdue_count || 0}</strong></article>
    </section>

    <section className="panel provider-status-panel">
      <div>
        <p className="eyebrow">Payment provider</p>
        <h3>{provider?.provider || 'demo'} <span className={`status status-${provider?.mode || 'demo'}`}>{provider?.mode || 'demo'}</span></h3>
        <p className="muted-copy">{provider?.configured ? 'Checkout credentials detected.' : 'Demo checkout is active until provider credentials are configured.'} Webhooks: {provider?.webhook_ready ? 'ready' : 'not configured'} · Live refunds: {provider?.live_refunds ? 'enabled' : 'disabled'}.</p>
      </div>
      <div className="provider-capabilities">{(provider?.capabilities || []).map((item) => <span className="tag" key={item}>{item}</span>)}</div>
    </section>

    <section className="panel">
      <div className="panel-heading"><div><p className="eyebrow">Collections</p><h3>Overdue invoices</h3></div><button className="button button-small" onClick={remind}>Generate reminders</button></div>
      {(data.overdue || []).map((invoice) => <div className="order-meta" key={invoice.id}><span><strong>{invoice.invoice_number}</strong> · {invoice.customer}</span><b>₹{Number(invoice.balance || 0).toLocaleString('en-IN')}</b></div>)}
      {!data.overdue?.length && <p className="muted-copy">No overdue invoices in the current workspace.</p>}
      {message && <div className="success-message">{message}</div>}
    </section>
  </AppShell>
}
