import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { login, register } from '../lib/api'

describe('authentication API adapter', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('API offline'))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('keeps a newly registered demo account available for login', async () => {
    await register('Fresh Client', 'fresh-client@example.com', 'Client1234')

    const result = await login('fresh-client@example.com', 'Client1234')

    expect(result.mode).toBe('demo')
    expect(result.user.email).toBe('fresh-client@example.com')
    expect(result.user.role).toBe('client')
  })
})
