import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RegisterPage from '../pages/RegisterPage'

const mocks = vi.hoisted(() => ({ signUp: vi.fn(), showModal: vi.fn() }))

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ signUp: mocks.signUp }),
}))

vi.mock('../context/ModalContext', () => ({
  useModal: () => ({ showModal: mocks.showModal }),
}))

describe('RegisterPage', () => {
  beforeEach(() => {
    mocks.signUp.mockReset().mockResolvedValue({ mode: 'demo' })
    mocks.showModal.mockReset()
  })

  it('requires a separate login after account creation', async () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'New Client' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new-client@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Client123' } })
    fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'Client123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument())
    expect(mocks.signUp).toHaveBeenCalledWith('New Client', 'new-client@example.com', 'Client123')
    expect(mocks.showModal).toHaveBeenCalledWith({
      type: 'success',
      title: 'Account created',
      message: 'Your account was created. Please sign in to continue.',
    })
  })
})
