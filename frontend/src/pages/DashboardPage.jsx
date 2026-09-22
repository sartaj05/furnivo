import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { useAuth } from '../context/AuthContext'
import { getLeads, getProducts, getQuotes } from '../lib/api'

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
  const { user, mode } = useAuth()
  const [metrics, setMetrics] = useState({ products: 0, quotes: 0, quoteValue: 0, leads: 0, followUps: 0, pipelineValue: 0 })
  const copy = roleCopy[user.role]

  useEffect(() => {
    async function loadMetrics() {
      const products = await getProducts().catch(() => ({ items: [] }))
      const quoteResult = ['admin', 'sales', 'designer'].includes(user.role) ? await getQuotes().catch(() => ({ items: [] })) : { items: [] }
      const leadResult = ['admin', 'sales'].includes(user.role) ? await getLeads().catch(() => ({ items: [] })) : { items: [] }
      const quotes = quoteResult.items || []
      const leads = leadResult.items || []
      setMetrics({
        products: (products.items || []).length,
        quotes: quotes.filter((quote) => quote.status !== 'Rejected').length,
        quoteValue: quotes.filter((quote) => quote.status !== 'Rejected').reduce((sum, quote) => sum + Number(quote.amount || 0), 0),
        leads: leads.filter((lead) => !['Won', 'Lost'].includes(lead.stage)).length,
        followUps: leads.reduce((sum, lead) => sum + (lead.tasks || []).filter((task) => !task.is_done).length, 0),
        pipelineValue: leads.filter((lead) => ['Qualified', 'Proposal'].includes(lead.stage)).reduce((sum, lead) => sum + Number(lead.value || 0), 0),
      })
    }
    loadMetrics()
  }, [user.role])

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
          <small>{mode === 'demo' ? 'Local demo data active' : 'Connected to live API'}</small>
        </div>
      </section>

      <section className="metric-grid">
        <article className="metric-card">
          <span>Catalog products</span>
          <strong>{metrics.products}</strong>
          <small>Active catalog products</small>
        </article>
        <article className="metric-card">
          <span>Open quotations</span>
          <strong>{metrics.quotes}</strong>
          <small>₹{metrics.quoteValue.toLocaleString('en-IN')} total value</small>
        </article>
        {(user.role === 'admin' || user.role === 'sales') && (
          <article className="metric-card">
            <span>Active leads</span>
            <strong>{metrics.leads}</strong>
            <small>{metrics.followUps} open follow-up tasks</small>
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
          <div className="accent-number">₹{metrics.pipelineValue.toLocaleString('en-IN')}</div>
          <small>Value currently in Qualified + Proposal</small>
        </article>
      </section>
    </AppShell>
  )
}
