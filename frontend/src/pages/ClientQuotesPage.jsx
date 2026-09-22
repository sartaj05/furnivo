import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { downloadQuotePdf, getClientQuotes, respondToQuote } from '../lib/api'

const actions = [
  { value: 'Approved', label: 'Approve quote' },
  { value: 'Change Requested', label: 'Request changes' },
  { value: 'Rejected', label: 'Reject quote' },
]

export default function ClientQuotesPage() {
  const [quotes, setQuotes] = useState([])
  const [comments, setComments] = useState({})
  const [error, setError] = useState('')

  async function load() {
    const result = await getClientQuotes()
    setQuotes(result.items || [])
  }

  useEffect(() => { load() }, [])

  async function respond(quote, action) {
    setError('')
    try {
      await respondToQuote(quote.database_id || quote.id, action, comments[quote.id] || '')
      await load()
    } catch (err) {
      setError(err.message || 'Unable to update quotation')
    }
  }

  return <AppShell title="My quotations" eyebrow="Review & approval">
    {error && <div className="form-error">{error}</div>}
    <section className="client-quote-grid">
      {quotes.map((quote) => <article className="panel client-quote-card" key={quote.id}>
        <div className="panel-heading"><div><p className="eyebrow">{quote.id} · {quote.date}</p><h3>{quote.customer}</h3></div><span className={`status status-${quote.status.toLowerCase().replaceAll(' ', '-')}`}>{quote.status}</span></div>
        <div className="client-quote-total"><span>Quotation total</span><strong>₹{Number(quote.amount || 0).toLocaleString('en-IN')}</strong></div>
        <p>{quote.items?.length ? `${quote.items.length} line items included.` : 'Commercial quotation ready for your review.'}</p>
        <textarea rows="3" placeholder="Add a comment or change request" value={comments[quote.id] || quote.client_access?.response_comment || ''} onChange={(e) => setComments({ ...comments, [quote.id]: e.target.value })} />
        <div className="card-actions"><button className="button-link" onClick={() => downloadQuotePdf(quote)}>Download PDF</button>{actions.map((action) => <button className={action.value === 'Approved' ? 'button button-small' : 'button-link'} key={action.value} onClick={() => respond(quote, action.value)}>{action.label}</button>)}</div>
      </article>)}
      {!quotes.length && <div className="empty-state panel"><h3>No quotations assigned yet</h3><p>Your sales team will share quotations here when they are ready.</p></div>}
    </section>
  </AppShell>
}
