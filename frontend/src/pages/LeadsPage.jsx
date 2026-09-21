import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getLeads, updateLeadStage } from '../lib/api'

const stages = ['New', 'Qualified', 'Proposal', 'Won']

export default function LeadsPage() {
  const [leads, setLeads] = useState([])

  async function load() {
    const result = await getLeads()
    setLeads(result.items)
  }

  useEffect(() => {
    load()
  }, [])

  async function changeStage(id, stage) {
    await updateLeadStage(id, stage)
    load()
  }

  return (
    <AppShell title="Lead CRM" eyebrow="Sales pipeline">
      <section className="crm-summary">
        {stages.map((stage) => {
          const stageLeads = leads.filter((lead) => lead.stage === stage)
          const total = stageLeads.reduce((sum, lead) => sum + Number(lead.value), 0)
          return (
            <div key={stage}>
              <span>{stage}</span>
              <strong>{stageLeads.length}</strong>
              <small>₹{total.toLocaleString('en-IN')}</small>
            </div>
          )
        })}
      </section>

      <section className="lead-grid">
        {leads.map((lead) => (
          <article className="lead-card" key={lead.id}>
            <div className="lead-top">
              <div>
                <h3>{lead.name}</h3>
                <p>{lead.company}</p>
              </div>
              <span className="source-chip">{lead.source}</span>
            </div>

            <div className="lead-details">
              <span>{lead.phone}</span>
              <strong>₹{Number(lead.value).toLocaleString('en-IN')}</strong>
            </div>

            <label>
              Pipeline stage
              <select value={lead.stage} onChange={(e) => changeStage(lead.id, e.target.value)}>
                {stages.map((stage) => <option key={stage}>{stage}</option>)}
              </select>
            </label>
          </article>
        ))}
      </section>
    </AppShell>
  )
}
