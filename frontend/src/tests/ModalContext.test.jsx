import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ModalProvider, useModal } from '../context/ModalContext'

function DemoTrigger() {
  const { showModal } = useModal()
  return <button onClick={() => showModal({ type: 'success', title: 'Saved', message: 'The furniture configuration was saved.' })}>Show message</button>
}

function InlineMessage() {
  return <div className="success-message">Quotation created successfully.</div>
}

describe('ModalProvider', () => {
  it('shows a centered success modal and closes it', () => {
    render(<ModalProvider><DemoTrigger /></ModalProvider>)
    fireEvent.click(screen.getByRole('button', { name: 'Show message' }))
    expect(screen.getByRole('dialog')).toHaveTextContent('The furniture configuration was saved.')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('converts existing page success messages into the global modal', async () => {
    render(<ModalProvider><InlineMessage /></ModalProvider>)
    await waitFor(() => expect(screen.getByRole('dialog')).toHaveTextContent('Quotation created successfully.'))
  })
})
