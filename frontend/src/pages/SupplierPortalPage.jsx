import { useEffect, useState } from 'react'
import { getSupplierPortal, updateSupplierPortalOrder } from '../lib/api'
import '../styles/supplier-portal.css'

export default function SupplierPortalPage() {
  const token = new URLSearchParams(window.location.search).get('token') || ''
  const [data, setData] = useState(null); const [error, setError] = useState(''); const [message, setMessage] = useState('')
  async function load() { setData(await getSupplierPortal(token)) }
  useEffect(() => { if (token) load().catch((err) => setError(err.message)); else setError('A supplier portal token is required.') }, [token])
  async function update(id, status) { try { await updateSupplierPortalOrder(token, id, { status }); setMessage('Purchase order updated.'); await load() } catch (err) { setError(err.message) } }
  return <main className="supplier-portal"><div className="supplier-portal-card"><p className="eyebrow">Furnivo supplier workspace</p><h1>{data?.supplier?.name || 'Supplier portal'}</h1><p className="muted-copy">Review purchase orders and keep delivery status current for the Furnivo team.</p>{error && <div className="form-error">{error}</div>}{message && <div className="success-message">{message}</div>}{data?.purchase_orders?.map((order) => <article className="supplier-order" key={order.id}><div><strong>{order.po_number}</strong><small>{order.items?.length || 0} items · Expected {order.expected_date || 'not set'}</small></div><select value={order.status} onChange={(event) => update(order.id, event.target.value)}><option>Draft</option><option>Confirmed</option><option>In transit</option><option>Received</option></select></article>)}{data && !data.purchase_orders?.length && <p className="muted-copy">No purchase orders are assigned to this supplier.</p>}</div></main>
}
