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

  it('keeps platform, why furnivo and contact on the landing page', () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>)
    expect(screen.getAllByRole('link', { name: 'Platform' })[0]).toHaveAttribute('href', '/?section=platform')
    expect(screen.getAllByRole('link', { name: 'Why Furnivo' })[0]).toHaveAttribute('href', '/?section=why-furnivo')
    expect(screen.getAllByRole('link', { name: 'Contact' })[0]).toHaveAttribute('href', '/?section=contact')
    expect(screen.getAllByRole('heading', { name: /tell us what you are building/i })[0]).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /send enquiry/i })[0]).toBeInTheDocument()
  })
})
