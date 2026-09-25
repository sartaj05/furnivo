import { describe, expect, it } from 'vitest'
import { canAccess, rolesFor, ROLE_HOME } from '../config/roleAccess'

describe('role access policy', () => {
  it('gives administrators full workspace access', () => {
    expect(canAccess('admin', '/app/access-control')).toBe(true)
    expect(canAccess('admin', '/app/project-portal')).toBe(true)
  })

  it('keeps operational controls away from sales and clients', () => {
    expect(canAccess('sales', '/app/leads')).toBe(true)
    expect(canAccess('sales', '/app/production')).toBe(false)
    expect(canAccess('client', '/app/inventory')).toBe(false)
    expect(canAccess('client', '/app/project-portal')).toBe(true)
  })

  it('provides a safe role-specific landing route', () => {
    expect(ROLE_HOME.sales).toBe('/app/leads')
    expect(ROLE_HOME.designer).toBe('/app/configurator')
    expect(rolesFor('/app/audit')).toEqual(['admin'])
  })
})

