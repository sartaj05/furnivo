import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createTenant, getTenants, switchTenant, updateTenantBranding, updateTenantSubscription } from '../lib/api'
import '../styles/tenant-billing.css'

export default function TenantWorkspaceEnhancedPage() {
  const [data, setData] = useState({ memberships: [], plans: {} }); const [name, setName] = useState(''); const [plan, setPlan] = useState('Growth'); const [branding, setBranding] = useState({ primary_color: '#234b3c', support_email: '' }); const [message, setMessage] = useState(''); const [error, setError] = useState('')
  async function load() { const result = await getTenants(); setData(result); const active = result.memberships?.find((item) => item.tenant.id === result.active_tenant_id)?.tenant; if (active) { setPlan(active.plan); setBranding({ primary_color: active.branding?.primary_color || '#234b3c', support_email: active.branding?.support_email || '' }) } }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  async function submit(event) { event.preventDefault(); try { await createTenant({ name }); setName(''); setMessage('Workspace created.'); await load() } catch (err) { setError(err.message) } }
  async function savePlan(id) { try { await updateTenantSubscription(id, { plan, status: 'active' }); setMessage(`${plan} plan selected.`); await load() } catch (err) { setError(err.message) } }
  async function saveBranding(id) { try { await updateTenantBranding(id, branding); setMessage('Branding saved.'); await load() } catch (err) { setError(err.message) } }
  async function choose(id) { try { await switchTenant(id); setMessage('Active workspace changed.'); await load() } catch (err) { setError(err.message) } }
  const active = data.memberships?.find((item) => item.tenant.id === data.active_tenant_id)?.tenant
  return <AppShell title="Tenant workspaces" eyebrow="SaaS workspaces, plans & custom branding">
    {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
    <section className="panel"><form className="mini-form" onSubmit={submit}><input required placeholder="New workspace name" value={name} onChange={(event) => setName(event.target.value)} /><button className="button">Create workspace</button></form></section>
    <section className="tenant-plan-grid">{Object.entries(data.plans || {}).map(([key, item]) => <article className={`panel tenant-plan ${plan === key ? 'selected' : ''}`} key={key}><p className="eyebrow">{key}</p><h3>{item.monthly_amount ? `INR ${item.monthly_amount.toLocaleString('en-IN')} / month` : 'Free trial'}</h3><p>{item.seats} seats · {item.limits.quotes_per_month} quotes/month</p><button className="button button-small" onClick={() => setPlan(key)}>{plan === key ? 'Selected' : 'Choose plan'}</button></article>)}</section>
    <section className="panel"><div className="panel-heading"><h3>Your workspaces</h3></div>{(data.memberships || []).map((item) => <div className="workspace-row" key={item.tenant.id}><span><strong>{item.tenant.name}</strong><small>{item.tenant.slug} · {item.tenant.plan} · {item.tenant.seat_limit} seat limit</small></span><span className="card-actions">{data.active_tenant_id === item.tenant.id ? <><b>Active</b><button className="button-link" onClick={() => savePlan(item.tenant.id)}>Save plan</button></> : <button className="button secondary" onClick={() => choose(item.tenant.id)}>Switch</button>}</span></div>)}</section>
    {active && <section className="panel branding-form"><div className="panel-heading"><div><p className="eyebrow">Custom branding</p><h3>{active.name}</h3></div></div><label>Primary color<input type="color" value={branding.primary_color} onChange={(event) => setBranding({ ...branding, primary_color: event.target.value })} /></label><label>Support email<input type="email" value={branding.support_email} onChange={(event) => setBranding({ ...branding, support_email: event.target.value })} /></label><button className="button button-small" onClick={() => saveBranding(active.id)}>Save branding</button></section>}
  </AppShell>
}
