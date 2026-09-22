import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/app', label: 'Overview', shortLabel: 'Home', roles: ['admin', 'sales', 'designer', 'client'], end: true },
  { to: '/app/catalog', label: 'Catalog', shortLabel: 'Catalog', roles: ['admin', 'sales', 'designer', 'client'] },
  { to: '/app/quotes', label: 'Quotations', shortLabel: 'Quotes', roles: ['admin', 'sales', 'designer'] },
  { to: '/app/customers', label: 'Customers', shortLabel: 'Clients', roles: ['admin', 'sales'] },
  { to: '/app/leads', label: 'Lead CRM', shortLabel: 'Leads', roles: ['admin', 'sales'] },
  { to: '/app/client-quotes', label: 'My quotations', shortLabel: 'Quotes', roles: ['client'] },
]

export default function AppShell({ title, eyebrow, actions, children }) {
  const { user, signOut, mode } = useAuth()
  const navigate = useNavigate()
  const allowedItems = navItems.filter((item) => item.roles.includes(user.role))

  function logout() {
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
