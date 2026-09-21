import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createQuote, getQuotes } from '../lib/api'

export default function QuotesPage() {
  const [quotes, setQuotes] = useState([])
  const [form, setForm] = useState({ customer: '', amount: '' })
  const [showForm, setShowForm] = useState(false)

  async function load() {
    const result = await getQuotes()
    setQuotes(result.items)
  }

  useEffect(() => {
    load()
  }, [])

  async function submit(e) {
    e.preventDefault()
    await createQuote(form)
    setForm({ customer: '', amount: '' })
    setShowForm(false)
    load()
  }

  return (
    <AppShell
      title="Quotations"
      eyebrow="Commercial documents"
      actions={
        <button className="button button-small" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Close' : 'New quotation'}
        </button>
      }
    >
      {showForm && (
        <form className="inline-form" onSubmit={submit}>
          <label>
            Customer / studio
            <input
              required
              value={form.customer}
              onChange={(e) => setForm({ ...form, customer: e.target.value })}
              placeholder="Northline Studio"
            />
          </label>
          <label>
            Quote amount
            <input
              required
              type="number"
              min="1"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
              placeholder="186400"
            />
          </label>
          <button className="button">Save draft</button>
        </form>
      )}

      <section className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Quote</th>
                <th>Customer</th>
                <th>Date</th>
                <th>Status</th>
                <th className="align-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {quotes.map((quote) => (
                <tr key={quote.id}>
                  <td data-label="Quote"><strong>{quote.id}</strong></td>
                  <td data-label="Customer">{quote.customer}</td>
                  <td data-label="Date">{quote.date}</td>
                  <td data-label="Status"><span className={`status status-${quote.status.toLowerCase()}`}>{quote.status}</span></td>
                  <td data-label="Amount" className="align-right">₹{Number(quote.amount).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  )
}
