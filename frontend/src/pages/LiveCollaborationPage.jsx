import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getLiveUpdates } from '../lib/api'

export default function LiveCollaborationPage() {
  const [items, setItems] = useState([]); const [mode, setMode] = useState('demo')
  async function load() { const result = await getLiveUpdates(); setItems(result.items || []); setMode(result.mode || 'demo') }
  useEffect(() => { load(); const timer = window.setInterval(load, 10000); return () => window.clearInterval(timer) }, [])
  return <AppShell title="Live collaboration" eyebrow="Shared activity feed & real-time workflow updates"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Connection: {mode}</p><h3>Workspace activity</h3></div><button className="button secondary" onClick={load}>Refresh</button></div>{items.map((item) => <div className="activity-row" key={item.id}><span><strong>{item.action}</strong><small>{item.resource_type} {item.resource_id ? `#${item.resource_id}` : ''} · {item.detail}</small></span><b>{new Date(item.created_at).toLocaleString()}</b></div>)}{!items.length && <p className="muted-copy">No new activity yet. Updates will appear here as your team changes quotes, production, inventory, and delivery records.</p>}</section></AppShell>
}
