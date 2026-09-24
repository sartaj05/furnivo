import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { disableMfa, enableMfa, getSecurityStatus, revokeAllSessions } from '../lib/api'
import '../styles/security-center.css'

export default function SecurityEnhancedPage() {
  const [security, setSecurity] = useState({ mfa_enabled: false, sessions: [], policy: {} }); const [message, setMessage] = useState(''); const [error, setError] = useState('')
  async function load() { setSecurity(await getSecurityStatus()) }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  async function action(fn, text) { setError(''); try { await fn(); setMessage(text); await load() } catch (err) { setError(err.message) } }
  const policy = security.policy || {}
  return <AppShell title="Security center" eyebrow="MFA, lockout policy & sessions">
    {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
    <section className="security-policy-grid">{[['MFA policy', policy.mfa_required_for_admin ? 'Required for admins' : 'Optional by account'], ['Login lockout', `${policy.max_login_attempts || 5} failed attempts`], ['Lockout window', `${policy.lockout_minutes || 15} minutes`], ['Password policy', `${policy.minimum_password_length || 10}+ characters`]].map(([label, value]) => <article className="panel security-policy-card" key={label}><p className="eyebrow">{label}</p><strong>{value}</strong></article>)}</section>
    <section className="security-grid"><article className="panel security-card"><p className="eyebrow">Multi-factor authentication</p><h3>{security.mfa_enabled ? 'MFA is enabled' : 'MFA is not enabled'}</h3><p className="muted-copy">Use time-limited one-time codes to protect sign-ins.</p><button className="button button-small" onClick={() => action(security.mfa_enabled ? disableMfa : enableMfa, security.mfa_enabled ? 'MFA disabled.' : 'MFA enabled.')}>{security.mfa_enabled ? 'Disable MFA' : 'Enable MFA'}</button></article><article className="panel security-card"><p className="eyebrow">Session control</p><h3>{security.sessions?.filter((session) => !session.revoked).length || 0} active sessions</h3><p className="muted-copy">Revoke refresh sessions if a device or token is suspected.</p><button className="button button-ghost button-small" onClick={() => action(revokeAllSessions, 'All sessions revoked.')}>Revoke all sessions</button></article></section>
    <section className="panel history-panel"><div className="panel-heading"><div><p className="eyebrow">Recent sessions</p><h3>Session history</h3></div></div>{security.sessions?.map((session) => <div className="session-row" key={session.id}><span><strong>{session.user_agent || 'Unknown browser'}</strong><small>{session.ip_address || 'Unknown IP'} · Created {new Date(session.created_at).toLocaleString()}</small></span><b>{session.revoked ? 'Revoked' : 'Active'}</b></div>)}</section>
  </AppShell>
}
