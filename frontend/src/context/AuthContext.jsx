import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../lib/api'
import { useModal } from './ModalContext'

const AuthContext = createContext(null)
export const SESSION_TIMEOUT_MS = 60 * 60 * 1000
const LAST_ACTIVITY_KEY = 'furnivo-last-activity'

function readStoredSession() {
  const savedUser = localStorage.getItem('furnivo-user')
  const savedToken = localStorage.getItem('furnivo-token')
  if (!savedUser && !savedToken) return { user: null, expired: false }

  try {
    const user = savedUser ? JSON.parse(savedUser) : null
    const lastActivity = Number(localStorage.getItem(LAST_ACTIVITY_KEY))
    const expired = !user || !savedToken || !lastActivity || Date.now() - lastActivity >= SESSION_TIMEOUT_MS
    return { user: expired ? null : user, expired }
  } catch {
    return { user: null, expired: true }
  }
}

function clearStoredSession() {
  localStorage.removeItem('furnivo-token')
  localStorage.removeItem('furnivo-user')
  localStorage.removeItem('furnivo-mode')
  localStorage.removeItem(LAST_ACTIVITY_KEY)
}

export function AuthProvider({ children }) {
  const { showModal } = useModal()
  const [initialSession] = useState(readStoredSession)
  const [user, setUser] = useState(initialSession.user)
  const [mode, setMode] = useState(() => localStorage.getItem('furnivo-mode') || 'demo')

  function expireSession() {
    clearStoredSession()
    setUser(null)
    setMode('demo')
    showModal({
      type: 'warning',
      title: 'Session expired',
      message: 'For your security, your session expired after 60 minutes without activity. Please sign in again.',
      duration: 0,
    })
  }

  useEffect(() => {
    if (!initialSession.expired) return undefined
    clearStoredSession()
    setMode('demo')
    showModal({
      type: 'warning',
      title: 'Session expired',
      message: 'Your previous session is no longer active. Please sign in again.',
      duration: 0,
    })
    return undefined
  }, [initialSession.expired, showModal])

  useEffect(() => {
    if (!user) return undefined

    let lastActivityWrite = 0

    function checkSession() {
      const lastActivity = Number(localStorage.getItem(LAST_ACTIVITY_KEY))
      if (!lastActivity || Date.now() - lastActivity >= SESSION_TIMEOUT_MS) {
        expireSession()
        return false
      }
      return true
    }

    function recordActivity() {
      if (!checkSession()) return
      const now = Date.now()
      if (now - lastActivityWrite > 10000) {
        localStorage.setItem(LAST_ACTIVITY_KEY, String(now))
        lastActivityWrite = now
      }
    }

    function handleVisibilityChange() {
      if (!document.hidden) checkSession()
    }

    function handleStorageChange(event) {
      if (event.key === 'furnivo-token' && !event.newValue) {
        setUser(null)
        setMode('demo')
      }
    }

    const events = ['click', 'keydown', 'mousemove', 'scroll', 'touchstart']
    events.forEach((eventName) => window.addEventListener(eventName, recordActivity, { passive: true }))
    window.addEventListener('storage', handleStorageChange)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    const timer = window.setInterval(checkSession, 30000)

    return () => {
      events.forEach((eventName) => window.removeEventListener(eventName, recordActivity))
      window.removeEventListener('storage', handleStorageChange)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.clearInterval(timer)
    }
  }, [user])

  useEffect(() => {
    function handleModeChange(event) {
      setMode(event.detail || localStorage.getItem('furnivo-mode') || 'demo')
    }

    window.addEventListener('furnivo-mode-change', handleModeChange)
    return () => window.removeEventListener('furnivo-mode-change', handleModeChange)
  }, [])

  function persistSession(result) {
    localStorage.setItem('furnivo-token', result.token)
    localStorage.setItem('furnivo-user', JSON.stringify(result.user))
    localStorage.setItem('furnivo-mode', result.mode || 'api')
    localStorage.setItem(LAST_ACTIVITY_KEY, String(Date.now()))
    setUser(result.user)
    setMode(result.mode || 'api')
    return result.user
  }

  async function signIn(email, password) {
    const result = await api.login(email, password)
    if (result.mfa_required) return result
    return persistSession(result)
  }

  async function verifyMfa(challengeId, code) {
    return persistSession(await api.verifyMfa(challengeId, code))
  }

  async function signUp(name, email, password) {
    // Registration creates credentials only. The user must explicitly sign in.
    return api.register(name, email, password)
  }

  function signOut() {
    clearStoredSession()
    setUser(null)
    setMode('demo')
  }

  const value = useMemo(
    () => ({ user, mode, signIn, signUp, signOut, verifyMfa, isAuthenticated: Boolean(user) }),
    [user, mode],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
