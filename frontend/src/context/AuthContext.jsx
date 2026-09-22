import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('furnivo-user')
    return saved ? JSON.parse(saved) : null
  })
  const [mode, setMode] = useState(() => localStorage.getItem('furnivo-mode') || 'demo')

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
    setUser(result.user)
    setMode(result.mode || 'api')
    return result.user
  }

  async function signIn(email, password) {
    return persistSession(await api.login(email, password))
  }

  async function signUp(name, email, password) {
    return persistSession(await api.register(name, email, password))
  }

  function signOut() {
    localStorage.removeItem('furnivo-token')
    localStorage.removeItem('furnivo-user')
    localStorage.removeItem('furnivo-mode')
    setUser(null)
  }

  const value = useMemo(
    () => ({ user, mode, signIn, signUp, signOut, isAuthenticated: Boolean(user) }),
    [user, mode],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
