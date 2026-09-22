import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createCheckout, createInvoice, getInvoices, getOrders, recordPayment } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function InvoicesPage() {
  const { user } = useAuth()
  const canManage = ['admin', 'sales'].includes(user.role)
  const [invoices, setInvoices] = useState([])
  const [orders, setOrders] = useState([])
  const [orderId, setOrderId] = useState('')
  const [payment, setPayment] = useState({ id: null, amount: '', method: 'Bank transfer', reference: '' })
  const [error, setError] = useState('')
  async function load() { setInvoices((await getInvoices()).items || []); if (canManage) setOrders((await getOrders()).items || []) }
  useEffect(() => { load() }, [])
  async function makeInvoice(event) { event.preventDefault(); setError(''); try { await createInvoice({ order_id: orderId }); setOrderId(''); await load() } catch (err) { setError(err.message) } }
  async function pay(event) { event.preventDefault(); try { await recordPayment(payment.id, { amount: payment.amount, method: payment.method, reference: payment.reference }); setPayment({ id: null, amount: '', method: 'Bank transfer', reference: '' }); await load() } catch (err) { setError(err.message) } }
  async function checkout(invoice) { try { const result = await createCheckout(invoice.id); window.open(result.item.checkout_url, '_blank') } catch (err) { setError(err.message) } }
  return <AppShell title="Invoices & payments" eyebrow="Commercial collection">
    {canManage && <form className="panel customer-editor" onSubmit={makeInvoice}><div className="panel-heading"><div><p className="eyebrow">Billing</p><h3>Generate invoice from order</h3></div></div><div className="form-grid form-grid-3"><label>Order<select required value={orderId} onChange={(e) => setOrderId(e.target.value)}><option value="">Choose order</option>{orders.map((order) => <option value={order.id} key={order.id}>{order.order_number} · {order.customer}</option>)}</select></label></div>{error && <div className="form-error">{error}</div>}<button className="button">Generate invoice</button></form>}
    <section className="invoice-grid">{invoices.map((invoice) => <article className="panel invoice-card" key={invoice.id}><div className="panel-heading"><div><p className="eyebrow">{invoice.invoice_number} · {invoice.order_number}</p><h3>{invoice.customer}</h3></div><span className={`status status-${invoice.status.toLowerCase().replaceAll(' ', '-')}`}>{invoice.status}</span></div><div className="invoice-total"><div><span>Total</span><strong>₹{Number(invoice.total || 0).toLocaleString('en-IN')}</strong></div><div><span>Balance</span><strong>₹{Number(invoice.balance || 0).toLocaleString('en-IN')}</strong></div></div><div className="order-meta"><span>Due {invoice.due_date || '—'}</span>{Number(invoice.balance) > 0 && <button className="button-link" onClick={() => checkout(invoice)}>Pay online</button>}</div>{canManage && Number(invoice.balance) > 0 && <form className="mini-form" onSubmit={pay}><input type="number" min="0.01" max={invoice.balance} step="0.01" placeholder="Payment amount" value={payment.id === invoice.id ? payment.amount : ''} onChange={(e) => setPayment({ ...payment, id: invoice.id, amount: e.target.value })} /><select value={payment.id === invoice.id ? payment.method : 'Bank transfer'} onChange={(e) => setPayment({ ...payment, id: invoice.id, method: e.target.value })}><option>Bank transfer</option><option>UPI</option><option>Cash</option><option>Card</option></select><button className="button button-small">Record payment</button></form>}<div className="history-list">{(invoice.payments || []).map((item) => <div className="history-item" key={item.id}><span>₹{Number(item.amount).toLocaleString('en-IN')} · {item.method}</span><small>{item.reference || 'No reference'}</small></div>)}</div></article>)}</section>
  </AppShell>
}
