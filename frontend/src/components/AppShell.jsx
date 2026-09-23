import { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { deliverNotification, getNotifications, logoutSession, markNotificationRead, retryNotificationDelivery } from '../lib/api'

const navItems = [
  { to: '/app', label: 'Overview', shortLabel: 'Home', roles: ['admin', 'sales', 'designer', 'client'], end: true },
  { to: '/app/catalog', label: 'Catalog', shortLabel: 'Catalog', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/quotes', label: 'Quotations', shortLabel: 'Quotes', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/configurator', label: 'Quote configurator', shortLabel: 'Configure', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/production', label: 'Production planning', shortLabel: 'Production', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/production-scheduling', label: 'Production scheduling', shortLabel: 'Calendar', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/quality-control', label: 'Quality control', shortLabel: 'Quality', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/customers', label: 'Customers', shortLabel: 'Clients', roles: ['admin', 'sales'] },
  { to: '/app/leads', label: 'Lead CRM', shortLabel: 'Leads', roles: ['admin', 'sales'] },
  { to: '/app/client-quotes', label: 'My quotations', shortLabel: 'Quotes', roles: ['client'] },
  { to: '/app/project-portal', label: 'My project portal', shortLabel: 'Portal', roles: ['client'] },
  { to: '/app/mobile-portal', label: 'Mobile self-service', shortLabel: 'Mobile', roles: ['client'] },
  { to: '/app/orders', label: 'Orders & projects', shortLabel: 'Orders', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/inventory', label: 'Inventory', shortLabel: 'Stock', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/inventory-forecast', label: 'Inventory forecasting', shortLabel: 'Forecast', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/recommendations', label: 'Furniture recommendations', shortLabel: 'Suggest', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/invoices', label: 'Invoices & payments', shortLabel: 'Invoices', roles: ['admin', 'sales', 'client'] },
  { to: '/app/gst', label: 'GST & e-invoicing', shortLabel: 'GST', roles: ['admin', 'sales', 'client'] },
  { to: '/app/payment-reconciliation', label: 'Payment reconciliation', shortLabel: 'Reconcile', roles: ['admin', 'sales', 'client'] },
  { to: '/app/contracts', label: 'Contracts & signatures', shortLabel: 'Contracts', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/procurement', label: 'Procurement', shortLabel: 'Buying', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/reports', label: 'Reports & exports', shortLabel: 'Reports', roles: ['admin', 'sales'] },
  { to: '/app/audit', label: 'Audit log', shortLabel: 'Audit', roles: ['admin'] },
  { to: '/app/operations', label: 'Operations', shortLabel: 'Ops', roles: ['admin'] },
  { to: '/app/security', label: 'Security settings', shortLabel: 'Security', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/data-admin', label: 'Data administration', shortLabel: 'Data', roles: ['admin'] },
  { to: '/app/access-control', label: 'Access & approvals', shortLabel: 'Access', roles: ['admin'] },
  { to: '/app/service', label: 'Warranty & service', shortLabel: 'Service', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/analytics', label: 'Analytics & forecasting', shortLabel: 'Analytics', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/business-control', label: 'Business control center', shortLabel: 'Control', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/integrations', label: 'Accounting integrations', shortLabel: 'ERP', roles: ['admin'] },
  { to: '/app/accounting-center', label: 'Accounting control center', shortLabel: 'Accounts', roles: ['admin', 'sales'] },
  { to: '/app/branch-security', label: 'Branches & security', shortLabel: 'Branches', roles: ['admin'] },
  { to: '/app/notification-automation', label: 'Notification automation', shortLabel: 'Notify', roles: ['admin', 'sales'] },
  { to: '/app/route-planning', label: 'Route planning', shortLabel: 'Routes', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/field-operations', label: 'Field operations', shortLabel: 'Field', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/schedules', label: 'Delivery & installation', shortLabel: 'Schedule', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/warehouses', label: 'Warehouses', shortLabel: 'Stock map', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/returns', label: 'Returns & refunds', shortLabel: 'Returns', roles: ['admin', 'sales', 'client'] },
]

export default function AppShell({ title, eyebrow, actions, children }) {
  const { user, signOut, mode } = useAuth()
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const allowedItems = navItems.filter((item) => item.roles.includes(user.role))

  async function loadNotifications() {
    const result = await getNotifications().catch(() => ({ items: [] }))
    setNotifications(result.items || [])
  }

  useEffect(() => {
    loadNotifications()
    const timer = window.setInterval(loadNotifications, 30000)
    return () => window.clearInterval(timer)
  }, [user.id])

  async function readNotification(item) {
    if (!item.is_read) {
      await markNotificationRead(item.id)
      setNotifications((current) => current.map((notification) => notification.id === item.id ? { ...notification, is_read: true } : notification))
    }
  }

  async function deliver(item, channel) {
    const recipient = channel === 'whatsapp' ? window.prompt('WhatsApp number with country code') : user.email
    if (!recipient) return
    const result = await deliverNotification(item.id, channel, recipient)
    setNotifications((current) => current.map((notification) => notification.id === item.id ? { ...notification, delivery_status: result.item?.status || 'queued', delivery_id: result.item?.id } : notification))
    window.alert(`${channel === 'email' ? 'Email' : 'WhatsApp'} delivery requested.`)
  }

  async function retryDelivery(item) {
    if (!item.delivery_id) return
    const result = await retryNotificationDelivery(item.delivery_id)
    setNotifications((current) => current.map((notification) => notification.id === item.id ? { ...notification, delivery_status: result.item?.status || 'pending' } : notification))
  }

  async function logout() {
    await logoutSession().catch(() => {})
    signOut()
    navigate('/')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand-row">
          <NavLink className="brand brand-app" to="/">
            <span className="brand-mark">F</span>
            <span>Furnivo</span>
          </NavLink>
          <span className={`mode-chip mobile-mode-chip ${mode === 'demo' ? 'demo' : ''}`}>
            {mode === 'demo' ? 'Demo' : 'Live'}
          </span>
        </div>

        <div className="profile-card">
          <div className="avatar">{user.name.slice(0, 1)}</div>
          <div className="profile-copy">
            <strong>{user.name}</strong>
            <span>{user.role}</span>
          </div>
        </div>

        <nav className="side-nav" aria-label="Workspace navigation">
          {allowedItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              <span className="nav-full-label">{item.label}</span>
              <span className="nav-short-label">{item.shortLabel}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="notification-wrap">
            <button className="text-button notification-button" onClick={() => setShowNotifications((value) => !value)}>Notifications {notifications.filter((item) => !item.is_read).length > 0 && <span className="notification-count">{notifications.filter((item) => !item.is_read).length}</span>}</button>
            {showNotifications && <div className="notification-panel"><strong>Notifications</strong>{notifications.length ? notifications.map((item) => <div className={`notification-item ${item.is_read ? 'read' : ''}`} key={item.id} onClick={() => readNotification(item)}><b>{item.title}</b><span>{item.body}</span><small>{new Date(item.created_at).toLocaleString()} · {item.delivery_status || 'in-app'}</small><div><button className="button-link" onClick={(event) => { event.stopPropagation(); deliver(item, 'email') }}>Email</button> <button className="button-link" onClick={(event) => { event.stopPropagation(); deliver(item, 'whatsapp') }}>WhatsApp</button>{['pending', 'pending_configuration', 'failed'].includes(item.delivery_status) && item.delivery_id && <button className="button-link" onClick={(event) => { event.stopPropagation(); retryDelivery(item) }}>Retry</button>}</div></div>) : <small>No new notifications.</small>}</div>}
          </div>
          <span className={`mode-chip desktop-mode-chip ${mode === 'demo' ? 'demo' : ''}`}>
            {mode === 'demo' ? 'Demo data active' : 'Live API'}
          </span>
          <button className="text-button" onClick={logout}>Sign out</button>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-header">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
          </div>
          <div className="app-header-actions">{actions}</div>
        </header>
        {children}
      </main>
    </div>
  )
}
