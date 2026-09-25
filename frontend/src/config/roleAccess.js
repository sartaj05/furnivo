export const ROLE_HOME = {
  admin: '/app',
  sales: '/app/leads',
  designer: '/app/configurator',
  client: '/app/project-portal',
  workshop_operator: '/app/mobile-workshop',
  installer: '/app/field-operations',
  accountant: '/app/accounting-center',
}

export const ROLE_LABELS = {
  admin: 'Administrator',
  sales: 'Sales workspace',
  designer: 'Design & production',
  client: 'Client portal',
  workshop_operator: 'Workshop execution',
  installer: 'Installer & driver',
  accountant: 'Accounting workspace',
}

// The admin role is intentionally added by rolesFor so every workspace route
// remains available to administrators, including customer-facing previews.
const routeRoles = {
  '/app': ['sales', 'designer', 'client', 'workshop_operator'],
  '/app/catalog': ['sales', 'designer', 'client'],
  '/app/quotes': ['sales', 'designer'],
  '/app/configurator': ['sales', 'designer'],
  '/app/production': ['designer'],
  '/app/production-scheduling': ['designer'],
  '/app/production-gantt': ['designer'],
  '/app/quality-control': ['designer'],
  '/app/ai-design-assistant': ['sales', 'designer', 'client'],
  '/app/live-collaboration': ['sales', 'designer', 'client'],
  '/app/customers': ['sales'],
  '/app/leads': ['sales'],
  '/app/client-quotes': ['client'],
  '/app/project-portal': ['client'],
  '/app/mobile-portal': ['client'],
  '/app/orders': ['sales', 'designer', 'client'],
  '/app/inventory': ['sales', 'designer'],
  '/app/inventory-forecast': ['designer'],
  '/app/predictive-analytics': ['designer'],
  '/app/recommendations': ['sales', 'designer', 'client'],
  '/app/invoices': ['sales', 'client', 'accountant'],
  '/app/gst': ['sales', 'client', 'accountant'],
  '/app/payment-reconciliation': ['sales', 'client', 'accountant'],
  '/app/contracts': ['sales', 'designer', 'client'],
  '/app/procurement': ['designer'],
  '/app/reports': ['sales'],
  '/app/audit': [],
  '/app/operations': [],
  '/app/security': ['sales', 'designer', 'client'],
  '/app/data-admin': [],
  '/app/access-control': [],
  '/app/staff-management': [],
  '/app/service': ['sales', 'designer', 'client'],
  '/app/analytics': ['sales', 'designer'],
  '/app/business-control': ['sales'],
  '/app/integrations': [],
  '/app/accounting-center': ['sales', 'accountant'],
  '/app/branch-security': [],
  '/app/notification-automation': ['sales'],
  '/app/automation-builder': ['sales'],
  '/app/route-planning': [],
  '/app/field-operations': ['designer', 'client', 'installer'],
  '/app/mobile-workshop': ['designer', 'workshop_operator'],
  '/app/schedules': ['sales', 'designer', 'client', 'installer'],
  '/app/warehouses': ['designer'],
  '/app/returns': ['sales', 'client'],
  '/app/tenant-workspaces': [],
}

export function rolesFor(path) {
  return ['admin', ...(routeRoles[path] || [])]
}

export function canAccess(role, path) {
  return rolesFor(path).includes(role)
}
