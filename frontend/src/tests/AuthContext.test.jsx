import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { ModalProvider } from '../context/ModalContext'
import { AuthProvider, SESSION_TIMEOUT_MS, useAuth } from '../context/AuthContext'

function SessionProbe() {
  const { user } = useAuth()
  return <span>{user ? user.name : 'signed out'}</span>
}

describe('AuthProvider session expiry', () => {
  beforeEach(() => localStorage.clear())

  it('does not restore a session that has been inactive for 60 minutes', async () => {
    localStorage.setItem('furnivo-user', JSON.stringify({ id: 1, name: 'Old User', role: 'admin' }))
    localStorage.setItem('furnivo-token', 'old-token')
    localStorage.setItem('furnivo-mode', 'demo')
    localStorage.setItem('furnivo-last-activity', String(Date.now() - SESSION_TIMEOUT_MS - 1))

    render(<ModalProvider><AuthProvider><SessionProbe /></AuthProvider></ModalProvider>)

    expect(screen.getByText('signed out')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('dialog')).toHaveTextContent('Session expired'))
    expect(localStorage.getItem('furnivo-token')).toBeNull()
    expect(localStorage.getItem('furnivo-user')).toBeNull()
  })
})
