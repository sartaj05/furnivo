import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'

const roleCopy = {
  admin: {
    title: 'Business overview',
    subtitle: 'Admin workspace',
    note: 'You can access catalog, quotations, leads and business-wide visibility.',
  },
  sales: {
    title: 'Sales workspace',
    subtitle: 'Sales pipeline',
    note: 'Focus on customer quotations, lead movement and current opportunity value.',
  },
  designer: {
    title: 'Design workspace',
    subtitle: 'Specification desk',
    note: 'Browse the product library and prepare quotation-ready selections.',
  },
  client: {
    title: 'Client workspace',
    subtitle: 'Project access',
    note: 'Browse curated products and keep the project experience simple.',
  },
}

export default function DashboardPage() {
  const { user } = useAuth()
  const copy = roleCopy[user.role]

  return (
    <AppShell title={copy.title} eyebrow={copy.subtitle}>
      <section className="welcome-card">
        <div>
          <span className="pill pill-white">{user.role}</span>
          <h2>Good afternoon, {user.name.split(' ')[0]}.</h2>
          <p>{copy.note}</p>
        </div>
        <div className="welcome-metric">
          <span>Workspace</span>
          <strong>Ready</strong>
          <small>Demo-safe data layer active</small>
        </div>
      </section>

      <section className="metric-grid">
        <article className="metric-card">
          <span>Catalog products</span>
          <strong>148</strong>
          <small>Across 12 active collections</small>
        </article>
        <article className="metric-card">
          <span>Open quotations</span>
          <strong>23</strong>
          <small>₹18.4L potential value</small>
        </article>
        {(user.role === 'admin' || user.role === 'sales') && (
          <article className="metric-card">
            <span>Active leads</span>
            <strong>31</strong>
            <small>8 need follow-up this week</small>
          </article>
        )}
        <article className="metric-card">
          <span>Conversion</span>
          <strong>28%</strong>
          <small>Rolling 90-day demo metric</small>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Recent activity</p>
              <h3>Commercial movement</h3>
            </div>
          </div>
          <div className="activity-list">
            <div><span className="activity-dot" /><p><strong>Northline Studio</strong> opened quotation Q-1042.</p><small>12 min ago</small></div>
            <div><span className="activity-dot" /><p><strong>SK Atelier</strong> entered the New lead stage.</p><small>1 hr ago</small></div>
            <div><span className="activity-dot" /><p><strong>Avenue Architects</strong> approved quotation Q-1038.</p><small>Yesterday</small></div>
          </div>
        </article>

        <article className="panel accent-panel">
          <p className="eyebrow eyebrow-light">This week</p>
          <h3>Keep the warm leads warm.</h3>
          <p>Eight active enquiries are due for follow-up. Prioritize qualified and proposal-stage opportunities while buyer intent is still fresh.</p>
          <div className="accent-number">₹7.35L</div>
          <small>Value currently in Qualified + Proposal</small>
        </article>
      </section>
    </AppShell>
  )
}
