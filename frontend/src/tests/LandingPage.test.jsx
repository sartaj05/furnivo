import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import LandingPage from '../pages/LandingPage'

describe('LandingPage', () => {
  it('renders the primary registration call to action', () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>)
    expect(screen.getByText('Sell the space,')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Create free demo account' })).toHaveAttribute('href', '/register')
  })
})
