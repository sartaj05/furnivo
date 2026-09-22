import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getAuditLogs } from '../lib/api'

export default function AuditPage() {
  const [logs, setLogs] = useState([]); const [resource, setResource] = useState('')
  async function load() { setLogs((await getAuditLogs(resource)).items || []) }
  useEffect(() => { load() }, [resource])
  return <AppShell title="Audit log" eyebrow="Security & accountability"><div className="toolbar"><select value={resource} onChange={(e) => setResource(e.target.value)}><option value="">All resources</option><option value="quote">Quotes</option><option value="invoice">Invoices</option><option value="inventory">Inventory</option><option value="purchase_order">Purchase orders</option><option value="notification">Notifications</option></select></div><section className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>When</th><th>User</th><th>Action</th><th>Resource</th><th>Detail</th></tr></thead><tbody>{logs.map((item) => <tr key={item.id}><td data-label="When">{new Date(item.created_at).toLocaleString()}</td><td data-label="User">{item.user?.name || 'System'}</td><td data-label="Action"><strong>{item.action}</strong></td><td data-label="Resource">{item.resource_type} {item.resource_id}</td><td data-label="Detail">{item.detail || '—'}</td></tr>)}</tbody></table></div></section></AppShell>
}
