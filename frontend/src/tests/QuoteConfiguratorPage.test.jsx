import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import QuoteConfiguratorPage from '../pages/QuoteConfiguratorPage'
import { ModalProvider } from '../context/ModalContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 2, name: 'Meera Sales', email: 'sales@furnivo.demo', role: 'sales' }, mode: 'demo', signOut: vi.fn() }),
}))

describe('QuoteConfiguratorPage', () => {
  it('loads the visual furniture configuration workspace', async () => {
    render(<ModalProvider><MemoryRouter><QuoteConfiguratorPage /></MemoryRouter></ModalProvider>)
    expect(screen.getByText('Furniture visual configurator')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Resume a configuration')).toBeInTheDocument())
    expect(screen.getByText('Saved specifications')).toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText('Villa living room set'), { target: { value: 'Test living room' } })
    expect(screen.getByDisplayValue('Test living room')).toBeInTheDocument()
  })
})
