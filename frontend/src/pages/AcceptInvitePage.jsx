import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { acceptStaffInvite } from '../lib/api'
import { useModal } from '../context/ModalContext'

export default function AcceptInvitePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { showModal } = useModal()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event) {
    event.preventDefault(); setError('')
    if (password !== confirm) return setError('Passwords do not match.')
    setSaving(true)
    try {
      await acceptStaffInvite(params.get('token') || '', password)
      showModal({ type: 'success', title: 'Invitation accepted', message: 'Your staff account is ready. Sign in to continue.' })
      navigate('/login', { replace: true })
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  return <main className="auth-page"><section className="login-card"><p className="eyebrow">Staff onboarding</p><h1>Set your Furnivo password</h1><p className="muted-copy">Your administrator invited you to join the workspace. Create a secure password to activate your account.</p><form className="login-form" onSubmit={submit}><label>Password<input required type="password" minLength="10" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="10+ characters" /></label><label>Confirm password<input required type="password" minLength="10" value={confirm} onChange={(event) => setConfirm(event.target.value)} placeholder="Repeat password" /></label>{error && <div className="form-error">{error}</div>}<button className="button" disabled={saving}>{saving ? 'Activating…' : 'Activate staff account'}</button></form><p className="auth-footnote"><Link to="/login">Back to sign in</Link></p></section></main>
}

