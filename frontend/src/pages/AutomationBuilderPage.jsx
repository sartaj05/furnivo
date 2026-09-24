import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getAutomationRules, toggleAutomationRule } from '../lib/api'
import '../styles/automation-builder.css'

export default function AutomationBuilderPage() {
  const [rules, setRules] = useState([]); const [error, setError] = useState(''); const [message, setMessage] = useState('')
  async function load() { setRules((await getAutomationRules()).rules || []) }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  async function toggle(rule) { setError(''); try { await toggleAutomationRule(rule.event, !rule.enabled); setMessage(`${rule.label} ${rule.enabled ? 'disabled' : 'enabled'}.`); await load() } catch (err) { setError(err.message) } }
  return <AppShell title="Workflow automation builder" eyebrow="Event rules, actions & approvals">
    {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Rule catalog</p><h3>Operational automations</h3></div><span className="mode-chip">Admin controlled</span></div>{rules.map((rule) => <div className="automation-rule" key={rule.event}><span><strong>{rule.label}</strong><small>When {rule.event.replaceAll('_', ' ')} → notify {rule.actions?.[0]?.channels?.join(', ') || 'in-app'} and write an audit event</small></span><button className={rule.enabled ? 'button button-small' : 'button button-ghost button-small'} onClick={() => toggle(rule)}>{rule.enabled ? 'Enabled' : 'Disabled'}</button></div>)}</section>
  </AppShell>
}
