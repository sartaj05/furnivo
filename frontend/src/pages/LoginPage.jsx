import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useModal } from '../context/ModalContext'

const demoAccounts = [
  ['Admin', 'admin@furnivo.demo', 'admin123'],
  ['Sales', 'sales@furnivo.demo', 'sales123'],
  ['Designer', 'designer@furnivo.demo', 'design123'],
  ['Client', 'client@furnivo.demo', 'client123'],
]

export default function LoginPage() {
  const navigate = useNavigate()
  const { signIn, verifyMfa } = useAuth()
  const { showModal } = useModal()
  const [form, setForm] = useState({
    email: 'admin@furnivo.demo',
    password: 'admin123',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [challenge, setChallenge] = useState(null)
  const [mfaCode, setMfaCode] = useState('')

  async function submit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await signIn(form.email, form.password)
      if (result?.mfa_required) { setChallenge(result); return }
      showModal({ type: 'success', title: 'Welcome back', message: 'You are signed in to your Furnivo workspace.' })
      navigate('/app')
    } catch (err) {
      setError(err.message || 'Unable to sign in')
    } finally {
      setLoading(false)
    }
  }

  async function submitMfa(event) {
    event.preventDefault(); setError(''); setLoading(true)
    try { await verifyMfa(challenge.challenge_id, mfaCode); showModal({ type: 'success', title: 'Welcome back', message: 'Verification complete. Your workspace is ready.' }); navigate('/app') } catch (err) { setError(err.message || 'Invalid MFA code') } finally { setLoading(false) }
  }

  function useAccount(email, password) {
    setForm({ email, password })
    setError('')
  }

  return (
    <div className="login-layout">
      <section className="login-story">
        <Link className="brand brand-light" to="/">
          <span className="brand-mark brand-mark-light">F</span>
          <span>Furnivo</span>
        </Link>

        <div className="login-story-copy">
          <p className="eyebrow eyebrow-light">Workspace access</p>
          <h1>Good systems should feel quieter than the work they organize.</h1>
          <p>
            Sign in to explore role-aware catalog, quotation and CRM workflows.
            The demo stays usable even without the Flask API.
          </p>
        </div>

        <div className="login-story-stat">
          <span>Demo architecture</span>
          <strong>React → API adapter → Flask or local fallback</strong>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={challenge ? submitMfa : submit}>
          <Link className="back-link" to="/">← Back to website</Link>
          <div className="login-heading">
            <p className="eyebrow">Welcome back</p>
            <h2>Sign in to Furnivo</h2>
            <p>Use any demo account below or your Flask-backed credentials.</p>
          </div>

          {!challenge && <><label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="name@company.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              required
            />
          </label></>}

          {challenge && <label>One-time verification code<input autoFocus inputMode="numeric" value={mfaCode} onChange={(e) => setMfaCode(e.target.value)} placeholder="6-digit code" required />{challenge.demo_code && <small className="field-hint">Demo code: {challenge.demo_code}</small>}</label>}

          {error && <div className="form-error">{error}</div>}

          <button className="button login-button" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="auth-switch">
            <Link className="forgot-link" to="/forgot-password">Forgot password?</Link>
          </p>

          <p className="auth-switch">
            New to Furnivo? <Link to="/register">Create an account</Link>
          </p>

          <div className="demo-box">
            <strong>Demo accounts</strong>
            <div className="demo-account-grid">
              {demoAccounts.map(([role, email, password]) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => useAccount(email, password)}
                >
                  <span>{role}</span>
                  <small>{email}</small>
                </button>
              ))}
            </div>
          </div>
        </form>
      </section>
    </div>
  )
}
