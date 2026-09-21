import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { signUp } = useAuth()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError('')

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await signUp(form.name, form.email, form.password)
      navigate('/app')
    } catch (err) {
      setError(err.message || 'Unable to create account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-layout auth-register-layout">
      <section className="login-story register-story">
        <Link className="brand brand-light" to="/">
          <span className="brand-mark brand-mark-light">F</span>
          <span>Furnivo</span>
        </Link>

        <div className="login-story-copy">
          <p className="eyebrow eyebrow-light">Create your workspace</p>
          <h1>Start with a cleaner buying and project experience.</h1>
          <p>
            New public registrations are created as client accounts. Internal sales,
            designer and admin roles stay controlled by the business.
          </p>
        </div>

        <div className="login-story-stat">
          <span>Demo-safe registration</span>
          <strong>Works with Flask or local browser storage</strong>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <Link className="back-link" to="/">← Back to website</Link>

          <div className="login-heading">
            <p className="eyebrow">New account</p>
            <h2>Create your account</h2>
            <p>Register once, then continue directly into the client workspace.</p>
          </div>

          <label>
            Full name
            <input
              type="text"
              autoComplete="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Your full name"
              required
            />
          </label>

          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="name@company.com"
              required
            />
          </label>

          <div className="form-two-col">
            <label>
              Password
              <input
                type="password"
                autoComplete="new-password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Minimum 6 characters"
                required
              />
            </label>

            <label>
              Confirm password
              <input
                type="password"
                autoComplete="new-password"
                value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                placeholder="Repeat password"
                required
              />
            </label>
          </div>

          {error && <div className="form-error" role="alert">{error}</div>}

          <button className="button login-button" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>

          <p className="auth-switch">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </section>
    </div>
  )
}
