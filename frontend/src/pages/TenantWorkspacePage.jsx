import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createTenant, getTenants, switchTenant } from '../lib/api'

export default function TenantWorkspacePage() {
  const [data, setData] = useState({ memberships: [], active_tenant_id: null }); const [name, setName] = useState(''); const [message, setMessage] = useState('')
  async function load() { setData(await getTenants()) }
  useEffect(() => { load() }, [])
  async function submit(event) { event.preventDefault(); if (!name.trim()) return; await createTenant({ name }); setName(''); setMessage('Workspace created.'); await load() }
  async function choose(id) { await switchTenant(id); setMessage('Active workspace changed.'); await load() }
  return <AppShell title="Tenant workspaces" eyebrow="Multi-company data boundaries & subscription plans"><section className="panel"><form className="mini-form" onSubmit={submit}><input placeholder="New workspace name" value={name} onChange={(e) => setName(e.target.value)} /><button className="button">Create workspace</button></form>{message && <div className="success-message">{message}</div>}</section><section className="panel"><div className="panel-heading"><h3>Your workspaces</h3></div>{(data.memberships || []).map((item) => <div className="workspace-row" key={item.tenant.id}><span><strong>{item.tenant.name}</strong><small>{item.tenant.slug} · {item.role} · {item.subscription?.plan || item.tenant.plan}</small></span>{data.active_tenant_id === item.tenant.id ? <b>Active</b> : <button className="button secondary" onClick={() => choose(item.tenant.id)}>Switch</button>}</div>)}{!data.memberships?.length && <p className="muted-copy">No workspace membership found.</p>}</section></AppShell>
}
