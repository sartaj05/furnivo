import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'
import { getDashboardMetrics } from '../lib/api'

const roleCopy = {
  admin: { title: 'Business overview', subtitle: 'Admin workspace', note: 'You can access catalog, quotations, leads and business-wide visibility.' },
  sales: { title: 'Sales workspace', subtitle: 'Sales pipeline', note: 'Focus on customer quotations, lead movement and current opportunity value.' },
  designer: { title: 'Design workspace', subtitle: 'Specification desk', note: 'Browse the product library and prepare quotation-ready selections.' },
  client: { title: 'Client workspace', subtitle: 'Project access', note: 'Browse curated products and keep the project experience simple.' },
}

export default function DashboardPage() {
  const { user, mode } = useAuth()
  const [dashboard, setDashboard] = useState({ cards: [], focus: '' })
  const copy = roleCopy[user.role] || roleCopy.client

  useEffect(() => {
    getDashboardMetrics().then(setDashboard).catch(() => setDashboard({ cards: [], focus: 'Dashboard metrics are temporarily unavailable.' }))
  }, [user.role])

  return <AppShell title={copy.title} eyebrow={copy.subtitle}>
    <section className="welcome-card"><div><span className="pill pill-white">{user.role}</span><h2>Good afternoon, {user.name.split(' ')[0]}.</h2><p>{copy.note}</p></div><div className="welcome-metric"><span>Workspace</span><strong>Ready</strong><small>{mode === 'demo' ? 'Local demo data active' : 'Connected to live API'}</small></div></section>
    <section className="metric-grid">{dashboard.cards.map((item) => <article className="metric-card" key={item.key}><span>{item.label}</span><strong>{item.display}</strong><small>{item.helper}</small></article>)}</section>
    <section className="content-grid"><article className="panel"><div className="panel-heading"><div><p className="eyebrow">Recent activity</p><h3>Commercial movement</h3></div></div><div className="activity-list"><div><span className="activity-dot" /><p><strong>Northline Studio</strong> opened quotation Q-1042.</p><small>12 min ago</small></div><div><span className="activity-dot" /><p><strong>SK Atelier</strong> entered the New lead stage.</p><small>1 hr ago</small></div><div><span className="activity-dot" /><p><strong>Avenue Architects</strong> approved quotation Q-1038.</p><small>Yesterday</small></div></div></article><article className="panel accent-panel"><p className="eyebrow eyebrow-light">Role focus</p><h3>{dashboard.focus || 'Your workspace is ready.'}</h3><p>These metrics are scoped to your role and assigned work.</p><div className="accent-number">{dashboard.cards.find((item) => ['pipeline', 'revenue'].includes(item.key))?.display || 'Ready'}</div><small>Current role-specific priority</small></article></section>
  </AppShell>
}
